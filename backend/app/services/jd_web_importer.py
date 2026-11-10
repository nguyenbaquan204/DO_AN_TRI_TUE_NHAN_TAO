"""Fetch and extract publicly accessible job descriptions from web pages.

This is a small, review-first importer. It deliberately does not bypass logins,
CAPTCHAs, or other access controls and never follows redirects to unvalidated
hosts.
"""

from __future__ import annotations

import html
import ipaddress
import json
import re
import socket
from html.parser import HTMLParser
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit

import httpx


MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_ROBOTS_BYTES = 512 * 1024
MAX_TEXT_CHARS = 60_000
MIN_VISIBLE_JD_CHARS = 300
BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "dd", "div", "dl",
    "dt", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2",
    "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "ol", "p",
    "section", "table", "td", "th", "tr", "ul",
}
IGNORED_TAGS = {"script", "style", "noscript", "svg", "iframe", "nav", "footer"}


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.visible_parts: list[str] = []
        self.semantic_parts: list[str] = []
        self.job_description_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.json_ld_parts: list[str] = []
        self._semantic_tags: list[str] = []
        self._job_description_tags: list[str] = []
        self._ignored_container_tags: list[str] = []
        self._title_depth = 0
        self._ignored_depth = 0
        self._script_is_json_ld = False
        self._script_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag == "meta":
            key = attrs.get("property") or attrs.get("name") or attrs.get("itemprop")
            if key and attrs.get("content"):
                self.meta[key.lower()] = attrs["content"].strip()
        if tag == "title":
            self._title_depth += 1
        itemprop = attrs.get("itemprop", "").lower()
        if tag in {"main", "article"} or itemprop in {"articlebody", "description"}:
            self._semantic_tags.append(tag)
        hints = " ".join((attrs.get(key, "") for key in ("class", "id", "data-testid", "itemprop"))).lower()
        if itemprop == "description" or re.search(
            r"(?:job|position|vacancy|posting)[_-]?(?:description|details|content)|"
            r"(?:description|details|content)[_-]?(?:job|position|vacancy)|jobdescription|jobdetails|vacancydescription",
            hints,
        ):
            self._job_description_tags.append(tag)
        if re.search(r"cookie|consent|feedback|support-widget|chat-widget|chatbot|cookie-banner|cookie-consent|onetrust|privacy-modal", hints):
            self._ignored_container_tags.append(tag)
            self._ignored_depth += 1
        if tag in IGNORED_TAGS:
            self._ignored_depth += 1
            if tag == "script":
                self._script_is_json_ld = "ld+json" in attrs.get("type", "").lower()
                self._script_parts = []
        if tag in BLOCK_TAGS and not self._ignored_depth:
            self.visible_parts.append("\n")
            if self._semantic_tags:
                self.semantic_parts.append("\n")
            if self._job_description_tags:
                self.job_description_parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        if tag == "script" and self._script_is_json_ld:
            self.json_ld_parts.append("".join(self._script_parts))
            self._script_is_json_ld = False
            self._script_parts = []
        if tag in IGNORED_TAGS and self._ignored_depth:
            self._ignored_depth -= 1
        if tag in self._ignored_container_tags:
            self._ignored_container_tags.pop(len(self._ignored_container_tags) - 1 - self._ignored_container_tags[::-1].index(tag))
            if self._ignored_depth:
                self._ignored_depth -= 1
        if tag in BLOCK_TAGS and not self._ignored_depth:
            self.visible_parts.append("\n")
            if self._semantic_tags:
                self.semantic_parts.append("\n")
            if self._job_description_tags:
                self.job_description_parts.append("\n")
        if tag in self._semantic_tags:
            self._semantic_tags.pop(len(self._semantic_tags) - 1 - self._semantic_tags[::-1].index(tag))
        if tag in self._job_description_tags:
            self._job_description_tags.pop(len(self._job_description_tags) - 1 - self._job_description_tags[::-1].index(tag))

    def handle_data(self, data):
        value = data.strip()
        if not value:
            return
        if self._title_depth:
            self.title_parts.append(value)
        if self._script_is_json_ld:
            self._script_parts.append(data)
        if not self._ignored_depth:
            self.visible_parts.append(value)
            if self._semantic_tags:
                self.semantic_parts.append(value)
            if self._job_description_tags:
                self.job_description_parts.append(value)


def _normalize_text(value: str) -> str:
    value = html.unescape(value or "").replace("\xa0", " ")
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r" *\n+ *", "\n", value)
    return value.strip()[:MAX_TEXT_CHARS]


def looks_like_job_listing(title: str, text: str) -> bool:
    heading_and_intro = f"{title}\n{text[:2_000]}"
    if re.search(r"\btuyển dụng\s+\d[\d.,]*\s+việc làm\b", heading_and_intro, re.I):
        return True
    repeated_job_actions = re.findall(r"\b(?:xem chi tiết|ứng tuyển ngay|apply now|view job)\b", text, re.I)
    return len(repeated_job_actions) >= 3


def _walk_job_postings(value):
    if isinstance(value, list):
        for item in value:
            yield from _walk_job_postings(item)
    elif isinstance(value, dict):
        kind = value.get("@type", "")
        if isinstance(kind, list):
            is_job = "JobPosting" in kind
        else:
            is_job = kind == "JobPosting"
        if is_job:
            yield value
        for key, item in value.items():
            if key in {"@graph", "mainEntity", "mainEntityOfPage"}:
                yield from _walk_job_postings(item)


def _schema_text(value) -> str:
    if isinstance(value, str):
        without_tags = re.sub(r"<[^>]*>", " ", html.unescape(value))
        return _normalize_text(without_tags)
    if isinstance(value, list):
        return " ".join(part for part in (_schema_text(item) for item in value) if part)
    if isinstance(value, dict):
        return _schema_text(value.get("name") or value.get("description") or value.get("value") or "")
    return ""


def _job_location(value) -> str:
    locations = value if isinstance(value, list) else [value]
    results = []
    for location in locations:
        if not isinstance(location, dict):
            continue
        address = location.get("address", {})
        if isinstance(address, str):
            results.append(address)
            continue
        if not isinstance(address, dict):
            continue
        parts = [address.get(key) for key in ("addressLocality", "addressRegion", "addressCountry")]
        parts = [part.get("name") if isinstance(part, dict) else part for part in parts]
        rendered = ", ".join(str(part).strip() for part in parts if part)
        if rendered:
            results.append(rendered)
    return "; ".join(dict.fromkeys(results))


def _public_http_url(url: str) -> str:
    parts = urlsplit((url or "").strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("Nhập một đường dẫn công khai bắt đầu bằng http:// hoặc https://.")
    if parts.username or parts.password:
        raise ValueError("Đường dẫn có thông tin đăng nhập không được hỗ trợ.")
    try:
        port = parts.port
    except ValueError:
        raise ValueError("Đường dẫn có cổng mạng không hợp lệ.") from None
    if port not in {None, 80, 443}:
        raise ValueError("Chỉ hỗ trợ trang web sử dụng cổng HTTP/HTTPS tiêu chuẩn.")
    host = parts.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError("Chỉ hỗ trợ tên miền công khai.")
    try:
        resolved = {ipaddress.ip_address(host)} if _is_ip_address(host) else {
            ipaddress.ip_address(entry[4][0]) for entry in socket.getaddrinfo(host, port or (443 if parts.scheme.lower() == "https" else 80), type=socket.SOCK_STREAM)
        }
    except (OSError, ValueError):
        raise ValueError("Không thể xác minh địa chỉ máy chủ của đường dẫn này.") from None
    if not resolved or any(not address.is_global for address in resolved):
        raise ValueError("Đường dẫn phải trỏ tới máy chủ có địa chỉ IP công khai.")
    return parts.geturl()


def _is_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _request_public_json(url: str) -> dict | list:
    """Read a JSON endpoint only after validating its public destination."""
    safe_url = _public_http_url(url)
    try:
        with httpx.Client(
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0),
            follow_redirects=False,
            trust_env=False,
            headers={"Accept": "application/json", "User-Agent": "AIRecruit-JD-Importer/1.0"},
        ) as client:
            with client.stream("GET", safe_url) as response:
                if response.is_redirect:
                    raise ValueError("API công khai chuyển hướng sang địa chỉ khác nên không thể nhập an toàn.")
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "json" not in content_type:
                    raise ValueError("Nguồn tuyển dụng không trả về dữ liệu JSON như dự kiến.")
                chunks = []
                size = 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_PAGE_BYTES:
                        raise ValueError("Dữ liệu tin tuyển dụng vượt quá giới hạn 2 MB.")
                    chunks.append(chunk)
                return json.loads(b"".join(chunks))
    except ValueError:
        raise
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise ValueError("Không tìm thấy tin công khai tại nguồn tuyển dụng này.") from None
        raise ValueError(f"API tuyển dụng từ chối yêu cầu (HTTP {exc.response.status_code}).") from None
    except (httpx.HTTPError, json.JSONDecodeError):
        raise ValueError("Không đọc được API tin tuyển dụng công khai. Hãy thử dán nội dung JD hoặc tải file lên.") from None


def _plain_html(value: str) -> str:
    parser = _PageParser()
    decoded = value or ""
    for _ in range(3):
        unescaped = html.unescape(decoded)
        if unescaped == decoded:
            break
        decoded = unescaped
    try:
        parser.feed(decoded)
    except Exception:
        return _normalize_text(re.sub(r"<[^>]*>", " ", decoded))
    return _normalize_text("\n".join(parser.visible_parts))


def _lever_posting(posting: dict, source_url: str) -> dict:
    categories = posting.get("categories") or {}
    description = posting.get("descriptionPlain") or posting.get("descriptionBodyPlain") or ""
    if not description:
        chunks = [posting.get("openingPlain", "")]
        chunks.extend(_plain_html(item.get("content", "")) for item in (posting.get("lists") or []) if isinstance(item, dict))
        chunks.append(posting.get("additionalPlain", ""))
        description = "\n\n".join(part for part in chunks if part)
    return {
        "source_url": posting.get("hostedUrl") or source_url,
        "title": _normalize_text(posting.get("text", ""))[:255],
        "company_name": "",
        "department": _normalize_text(categories.get("team") or categories.get("department") or "")[:255],
        "location": _normalize_text(categories.get("location") or ", ".join(categories.get("allLocations") or []))[:255],
        "employment_type": _normalize_text(categories.get("commitment") or "")[:100],
        "experience_required": "",
        "education_required": "",
        "description": _normalize_text(description)[:MAX_TEXT_CHARS],
        "extraction_method": "Lever public postings API",
    }


def _greenhouse_posting(posting: dict, source_url: str, company_name: str = "") -> dict:
    location = posting.get("location") or {}
    location_name = location.get("name", "") if isinstance(location, dict) else str(location or "")
    departments = posting.get("departments") or []
    department = ", ".join(item.get("name", "") for item in departments if isinstance(item, dict) and item.get("name"))
    description = posting.get("content") or posting.get("description") or ""
    return {
        "source_url": posting.get("absolute_url") or source_url,
        "title": _normalize_text(posting.get("title", ""))[:255],
        "company_name": _normalize_text(company_name)[:255],
        "department": _normalize_text(department)[:255],
        "location": _normalize_text(location_name)[:255],
        "employment_type": "",
        "experience_required": "",
        "education_required": "",
        "description": _plain_html(description)[:MAX_TEXT_CHARS],
        "extraction_method": "Greenhouse public Job Board API",
    }


def _fetch_lever_url(url: str) -> dict:
    parts = urlsplit(_public_http_url(url))
    host = (parts.hostname or "").lower()
    if host not in {"jobs.lever.co", "jobs.eu.lever.co"}:
        raise ValueError("URL Lever không hợp lệ.")
    segments = [segment for segment in parts.path.split("/") if segment]
    if not segments or not re.fullmatch(r"[A-Za-z0-9_-]+", segments[0]):
        raise ValueError("Không xác định được tên bảng tin Lever từ đường dẫn.")
    site = segments[0]
    api_host = "api.eu.lever.co" if host == "jobs.eu.lever.co" else "api.lever.co"
    base = f"https://{api_host}/v0/postings/{site}"
    if len(segments) > 1 and re.fullmatch(r"[A-Fa-f0-9-]{16,64}", segments[1]):
        posting = _request_public_json(f"{base}/{segments[1]}")
        if not isinstance(posting, dict):
            raise ValueError("Dữ liệu tin Lever không đúng định dạng.")
        return _lever_posting(posting, url)
    postings = _request_public_json(f"{base}?mode=json&limit=100")
    if not isinstance(postings, list):
        raise ValueError("Danh sách việc làm Lever không đúng định dạng.")
    result = [_lever_posting(item, url) for item in postings if isinstance(item, dict)]
    if not result:
        raise ValueError("Bảng tin Lever này hiện không có tin công khai.")
    return {"source_url": url, "postings": result, "extraction_method": "Lever public postings API"}


def _fetch_greenhouse_url(url: str) -> dict:
    parts = urlsplit(_public_http_url(url))
    host = (parts.hostname or "").lower()
    if host not in {"boards.greenhouse.io", "job-boards.greenhouse.io"}:
        raise ValueError("URL Greenhouse không hợp lệ.")
    segments = [segment for segment in parts.path.split("/") if segment]
    if not segments or not re.fullmatch(r"[A-Za-z0-9_-]+", segments[0]):
        raise ValueError("Không xác định được mã bảng tin Greenhouse từ đường dẫn.")
    token = segments[0]
    base = f"https://boards-api.greenhouse.io/v1/boards/{token}"
    company = _request_public_json(base)
    company_name = company.get("name", "") if isinstance(company, dict) else ""
    job_index = next((index for index, segment in enumerate(segments) if segment == "jobs"), None)
    if job_index is not None and job_index + 1 < len(segments) and segments[job_index + 1].isdigit():
        posting = _request_public_json(f"{base}/jobs/{segments[job_index + 1]}?content=true")
        if not isinstance(posting, dict):
            raise ValueError("Dữ liệu tin Greenhouse không đúng định dạng.")
        return _greenhouse_posting(posting, url, company_name)
    postings_data = _request_public_json(f"{base}/jobs?content=true")
    postings = postings_data.get("jobs", []) if isinstance(postings_data, dict) else []
    result = [_greenhouse_posting(item, url, company_name) for item in postings if isinstance(item, dict)]
    if not result:
        raise ValueError("Bảng tin Greenhouse này hiện không có tin công khai.")
    return {"source_url": url, "postings": result, "extraction_method": "Greenhouse public Job Board API"}


def _fetch_ats_url(url: str) -> dict | None:
    parts = urlsplit((url or "").strip())
    host = (parts.hostname or "").lower()
    if host in {"jobs.lever.co", "jobs.eu.lever.co"}:
        return _fetch_lever_url(url)
    if host in {"boards.greenhouse.io", "job-boards.greenhouse.io"}:
        return _fetch_greenhouse_url(url)
    return None


def fetch_job_page(url: str) -> dict:
    safe_url = _public_http_url(url)
    ats_result = _fetch_ats_url(safe_url)
    if ats_result is not None:
        return ats_result
    parts = urlsplit(safe_url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        with httpx.Client(
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0),
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": "AIRecruit-JD-Importer/1.0 (public job description import)"},
        ) as client:
            robots_lines = None
            try:
                with client.stream("GET", robots_url) as robots_response:
                    if 300 <= robots_response.status_code < 400:
                        raise ValueError("Không thể xác minh robots.txt vì trang chuyển hướng.")
                    if robots_response.status_code in {401, 403, 429}:
                        raise ValueError("Website từ chối truy cập robots.txt nên không thể kiểm tra quyền đọc tự động.")
                    if 500 <= robots_response.status_code < 600:
                        raise ValueError("Website đang lỗi khi kiểm tra robots.txt; hãy thử lại sau.")
                    if robots_response.status_code < 400:
                        robots_size = 0
                        robots_chunks = []
                        for chunk in robots_response.iter_bytes():
                            robots_size += len(chunk)
                            if robots_size > MAX_ROBOTS_BYTES:
                                raise ValueError("Tệp robots.txt quá lớn để kiểm tra.")
                            robots_chunks.append(chunk)
                        robots_body = b"".join(robots_chunks).decode("utf-8", errors="replace")
                        robots_lines = robots_body.splitlines()
            except httpx.HTTPStatusError:
                robots_lines = None
            except httpx.HTTPError:
                raise ValueError("Không thể xác minh robots.txt của website; hãy thử lại sau.") from None

            if robots_lines is not None:
                robots = RobotFileParser(robots_url)
                robots.parse(robots_lines)
                if not robots.can_fetch("AIRecruit-JD-Importer", safe_url):
                    raise ValueError("Website không cho phép trình nhập tự động đọc đường dẫn này theo robots.txt.")

            with client.stream("GET", safe_url) as response:
                if response.is_redirect:
                    raise ValueError("Trang chuyển hướng sang địa chỉ khác; hãy mở đường dẫn đích và nhập lại.")
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                    raise ValueError("Đường dẫn này không trả về trang HTML công khai.")
                chunks = []
                size = 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_PAGE_BYTES:
                        raise ValueError("Trang quá lớn để nhập (giới hạn 2 MB).")
                    chunks.append(chunk)
                body = b"".join(chunks)
                encoding = response.encoding or "utf-8"
                source_page = body.decode(encoding, errors="replace")
    except ValueError:
        raise
    except httpx.HTTPStatusError as exc:
        raise ValueError(f"Trang từ chối yêu cầu (HTTP {exc.response.status_code}).") from None
    except httpx.HTTPError:
        raise ValueError("Không tải được trang. Trang có thể chặn yêu cầu tự động hoặc đang tạm thời không hoạt động.") from None

    parser = _PageParser()
    try:
        parser.feed(source_page)
    except Exception:
        raise ValueError("Không đọc được cấu trúc trang HTML này.") from None

    page_title = _normalize_text(" ".join(parser.title_parts))
    visible_text = _normalize_text("\n".join(parser.visible_parts))
    if looks_like_job_listing(page_title, visible_text):
        raise ValueError(
            "Đây là trang tìm kiếm hoặc danh sách nhiều tin tuyển dụng, không phải trang chi tiết của một vị trí. "
            "Hãy mở một tin cụ thể rồi nhập đường dẫn đó, hoặc tải file/dán riêng phần mô tả công việc."
        )

    posting = None
    for raw_json in parser.json_ld_parts:
        try:
            parsed = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            continue
        posting = next(_walk_job_postings(parsed), None)
        if posting:
            break

    if posting:
        title = _schema_text(posting.get("title"))
        description = _schema_text(posting.get("description"))
        company = _schema_text(posting.get("hiringOrganization"))
        location = _job_location(posting.get("jobLocation"))
        employment_type = _schema_text(posting.get("employmentType"))
        experience = _schema_text(posting.get("experienceRequirements"))
        education = _schema_text(posting.get("educationRequirements"))
        extraction_method = "JobPosting structured data"
    else:
        title = ""
        description = ""
        company = ""
        location = ""
        employment_type = ""
        experience = ""
        education = ""
        extraction_method = "Visible page text"

    title = title or parser.meta.get("og:title") or page_title
    if not description:
        job_description_text = _normalize_text("\n".join(parser.job_description_parts))
        semantic_text = _normalize_text("\n".join(parser.semantic_parts))
        metadata_summary = _normalize_text(parser.meta.get("og:description") or parser.meta.get("description") or "")
        description = (
            job_description_text if len(job_description_text) >= MIN_VISIBLE_JD_CHARS
            else semantic_text if len(semantic_text) >= MIN_VISIBLE_JD_CHARS
            else metadata_summary
        )
        if len(description) < MIN_VISIBLE_JD_CHARS or (description == metadata_summary and metadata_summary.endswith(("...", "…"))):
            raise ValueError(
                "Không tìm được riêng phần mô tả công việc trong trang này; trang có thể dùng JavaScript hoặc không đánh dấu vùng JD. "
                "Hãy mở trang chi tiết của một tin, hoặc tải file/dán phần mô tả để tránh nhập lẫn nội dung toàn website."
            )
    return {
        "source_url": safe_url,
        "title": title[:255],
        "company_name": company[:255],
        "department": "",
        "location": location[:255],
        "employment_type": employment_type[:100],
        "experience_required": experience[:50],
        "education_required": education[:255],
        "description": description[:MAX_TEXT_CHARS],
        "extraction_method": extraction_method,
    }
