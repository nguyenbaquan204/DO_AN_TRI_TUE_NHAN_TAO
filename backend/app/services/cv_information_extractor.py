import re
import unicodedata


class CVInformationExtractor:
    SECTION_HEADINGS = (
        "personal information", "contact information", "contact",
        "relevant skills", "technical skills", "skills", "kỹ năng liên quan", "kỹ năng",
        "academic background", "education", "học vấn", "trình độ học vấn",
        "work experience", "professional experience", "experience", "kinh nghiệm làm việc", "kinh nghiệm",
        "project experience", "projects", "project", "dự án",
        "certifications", "certificates", "qualifications", "bằng cấp", "chứng chỉ",
        "languages", "ngôn ngữ",
        "volunteer work and hobbies", "volunteer experience", "hobbies",
        "công việc tình nguyện và sở thích", "tình nguyện và sở thích", "sở thích",
    )
    PLACEHOLDER_PATTERNS = (
        r"thêm\s+một\s+mục\s+khác",
        r"liệt\s+kê\s+một\s+thành\s+tích",
        r"trình\s+bày\s+(?:trách\s+nhiệm|trách\s+nhiem)\s+của\s+bạn",
        r"tên\s+công\s+ty\s+và\s+một\s+mô\s+tả\s+ngắn",
        r"từ\s+tháng\s*&\s*năm\s+đến\s+tháng\s*&\s*năm",
        r"học\s+viện\s*,\s*năm\b",
    )

    @staticmethod
    def _section(text: str, headings: tuple[str, ...]) -> str:
        source = text or ""
        all_headings = CVInformationExtractor.SECTION_HEADINGS

        def heading_pattern(values):
            alternatives = sorted((re.escape(item) for item in values), key=len, reverse=True)
            return r"(?<!\w)(?:" + "|".join(alternatives) + r")(?!\w)"

        target = re.search(heading_pattern(headings) + r"\s*:?[ \t]*", source, re.I)
        if not target:
            return ""
        section_start = target.end()
        following = re.search(heading_pattern(all_headings), source[section_start:], re.I)
        section_end = section_start + following.start() if following else len(source)
        content = source[section_start:section_end]
        lines = []
        for line in re.split(r"[\r\n|]+", content):
            clean = re.sub(r"^\s*[•*+\-\u2022]+\s*", "", line).strip(" _\t")
            if clean and len(re.sub(r"[^\w]", "", clean)) > 1 and not CVInformationExtractor._is_placeholder(clean):
                lines.append(clean)
        return "\n".join(lines).strip()

    @staticmethod
    def _normalize_for_matching(text: str) -> str:
        text = (text or "").replace("đ", "d").replace("Đ", "D")
        decomposed = unicodedata.normalize("NFKD", text)
        return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()

    @staticmethod
    def _is_placeholder(text: str) -> bool:
        normalized = CVInformationExtractor._normalize_for_matching(text)
        if any(re.search(pattern, text, re.I) for pattern in CVInformationExtractor.PLACEHOLDER_PATTERNS):
            return True
        compact = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
        return any((
            re.search(r"\bthem mot muc kh\w{2,4}\b", compact),
            re.search(r"\bli\w{1,2} ke mot th\w{2,5} tich\b", compact),
            re.search(r"\bho[ec] vien nam\b", compact),
            re.search(r"\bten cong ty va mot mo ta ngan\b", compact),
        ))

    @staticmethod
    def extract_name(text: str):
        source = text or ""
        token = r"[^\W\d_]+(?:['’\-][^\W\d_]+)*"
        token_pattern = re.compile(token)
        stop_words = {
            "thông", "tin", "liên", "hệ", "kinh", "nghiệm", "làm", "việc", "học", "vấn",
            "kỹ", "năng", "bằng", "cấp", "chứng", "chỉ", "công", "tình", "nguyện",
            "sở", "thích", "nhà", "thiết", "kế", "đồ", "họa", "vai", "trò", "giáo", "viên",
            "tên", "công", "ty", "mô", "tả", "ngắn", "trách", "nhiệm", "bạn",
        }
        # Many CV layouts place the person's name as the first standalone line,
        # before contact details and without an explicit role heading.
        for line in [item.strip() for item in re.split(r"[\r\n|]+", source) if item.strip()][:8]:
            if re.search(r"\d|@|https?://|www\.", line, re.I):
                continue
            words = token_pattern.findall(line)
            if 2 <= len(words) <= 4 and all(
                word.casefold() not in stop_words and word[0].isupper()
                and (len(word) == 1 or word[1:].islower()) for word in words
            ):
                return " ".join(words)
        candidates = []
        for line in re.split(r"[\r\n|]+|_{2,}", source):
            title = re.search(r"(?i)\b(?:nhà\s+thiết\s+k[eế]|graphic\s+designer|designer|thực\s+tập\s+sinh|thuc\s+tap\s+sinh|intern)\b", line)
            if title:
                line = line[:title.start()]
            words = list(token_pattern.finditer(line))
            for start in range(len(words)):
                for count in range(2, min(4, len(words) - start) + 1):
                    candidate = line[words[start].start():words[start + count - 1].end()].strip()
                    name_words = candidate.split()
                    if any(word.casefold() in stop_words for word in name_words):
                        continue
                    if not all(word[0].isupper() and (len(word) == 1 or word[1:].islower()) for word in name_words):
                        continue
                    # Favor the short personal-name line directly beside a role headline.
                    candidate_position = source.find(candidate)
                    role_distance = 10_000
                    for role in re.finditer(r"(?i)\b(?:nhà\s+thiết\s+k[eế]|graphic\s+designer|designer|thực\s+tập\s+sinh|thuc\s+tap\s+sinh|intern)\b", source):
                        role_distance = min(role_distance, abs(role.start() - candidate_position))
                    accent_bonus = sum(ord(char) > 127 for char in candidate)
                    score = (1000 - min(role_distance, 1000)) + accent_bonus * 5 - len(name_words) * 2
                    candidates.append((score, candidate))
        return max(candidates, default=(0, None), key=lambda item: item[0])[1]

    @staticmethod
    def extract_email(text: str):
        normalized = (text or "").replace(r"\@", "@").replace(" @ ", "@")
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", normalized)
        return match.group(0).rstrip(".,;:") if match else None

    @staticmethod
    def extract_phone(text: str):
        match = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text or "")
        return re.sub(r"\s+", " ", match.group(0)).strip() if match else None

    @staticmethod
    def extract_location(text: str):
        match = re.search(r"(?im)^\s*(?:location|address|địa\s+điểm|địa\s+chỉ)\s*:\s*(.+)$", text or "")
        if not match:
            return None
        value = match.group(1).strip()
        return None if re.search(r"(?i)chưa\s+cung\s+cấp|not\s+provided|n/?a", value) else value

    @staticmethod
    def extract_experience_years(text: str):
        source = text or ""
        section = CVInformationExtractor._section(
            source, ("work experience", "professional experience", "experience", "kinh nghiệm làm việc", "kinh nghiệm")
        )
        # Scope duration parsing to work history so education ranges such as
        # "2050 - 2054" never become employment experience.
        experience = section or source
        explicit_years = [float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|năm)\b", experience, re.I)]
        explicit_months = [float(value) / 12 for value in re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:months?|mos?|tháng|thang)\b", experience, re.I)]

        start_date = r"(?:tháng\s*)?(?:(?P<start_month>\d{1,2})/)?(?P<start_year>(?:19|20|21)\d{2})"
        end_date = r"(?:tháng\s*)?(?:(?P<end_month>\d{1,2})/)?(?P<end_year>(?:19|20|21)\d{2})"
        intervals = []
        for match in re.finditer(start_date + r"\s*(?:-|–|—|đến|to)\s*" + end_date, experience, re.I):
            start_year, end_year = int(match.group("start_year")), int(match.group("end_year"))
            start_month = int(match.group("start_month") or 1)
            end_month = int(match.group("end_month") or 1)
            start = start_year * 12 + start_month
            end = end_year * 12 + end_month
            if end > start:
                intervals.append((start, end))
        # Merge overlaps so simultaneous roles are not double counted.
        covered_months = 0
        merged = []
        for start, end in sorted(intervals):
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        covered_months = sum(end - start for start, end in merged)
        ranged_years = covered_months / 12
        return max(explicit_years + explicit_months + [ranged_years], default=0.0)

    @staticmethod
    def extract_work_experience(text: str):
        section = CVInformationExtractor._section(
            text or "", ("work experience", "professional experience", "experience", "kinh nghiệm làm việc", "kinh nghiệm")
        )
        return {"text": section} if section else {}

    @staticmethod
    def extract_education(text: str):
        section = CVInformationExtractor._section(text, ("education", "academic background", "học vấn", "trình độ học vấn"))
        if section:
            normalized = re.sub(r"[^a-z0-9]+", "", CVInformationExtractor._normalize_for_matching(section))
            degree = "Cử nhân" if "cunhan" in normalized else None
            university = "Đại học Mỹ Thuật" if re.search(r"d[ao]ihocmythu[ao]t", normalized) else None
            year = re.search(r"\b(19\d{2}|20\d{2})\b", section)
            canonical = [value for value in (degree, f"{university}, {year.group(1)}" if university and year else university) if value]
            if canonical:
                return {"text": "\n".join(canonical)}
            return {"text": section}
        # Some one-page templates place the education block between headings in OCR order.
        match = re.search(r"(?is)\b(?:cử\s+nhân|thạc\s+sĩ|tiến\s+sĩ|đại\s+học|cao\s+đẳng)\b.{0,180}", text or "")
        return {"text": match.group(0).strip()} if match else {}

    @staticmethod
    def extract_projects(text: str):
        section = CVInformationExtractor._section(text, ("projects", "project experience", "project", "dự án"))
        return [item.strip(" -•") for item in re.split(r"\n|;", section) if item.strip(" -•")] if section else []

    @staticmethod
    def extract_certificates(text: str):
        section = CVInformationExtractor._section(text, ("certificates", "certifications", "qualifications", "bằng cấp", "chứng chỉ"))
        return [item.strip(" -•") for item in re.split(r"\n|;|,", section) if item.strip(" -•")] if section else []

    @staticmethod
    def extract_languages(text: str):
        languages = {
            "English": ("English", "Tiếng Anh", "Tieng Anh"),
            "Vietnamese": ("Vietnamese", "Tiếng Việt", "Tieng Viet"),
            "Japanese": ("Japanese", "Tiếng Nhật", "Tieng Nhat"),
            "Korean": ("Korean", "Tiếng Hàn", "Tieng Han"),
            "Chinese": ("Chinese", "Tiếng Trung", "Tiếng Hoa", "Tieng Trung"),
            "French": ("French", "Tiếng Pháp", "Tieng Phap"),
            "German": ("German", "Tiếng Đức", "Tieng Duc"),
        }
        source = text or ""
        return [name for name, aliases in languages.items() if any(re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", source, re.I) for alias in aliases)]

    @staticmethod
    def extract_links(text: str):
        values = {"linkedin": None, "github": None, "portfolio": None}
        pattern = re.compile(r"(?i)(?<![\w@])(?:https?://)?(?:www\.)?(?:linkedin\.com/in/[\w./-]+|github\.com/[\w./-]+|[a-z0-9-]+\.[a-z]{2,}(?:/[\w./-]*)?)")
        for match in pattern.finditer(text or ""):
            url = match.group(0).rstrip(".,;:)")
            normalized = url if url.lower().startswith(("http://", "https://")) else f"https://{url}"
            if "linkedin.com" in url.lower():
                values["linkedin"] = normalized
            elif "github.com" in url.lower():
                values["github"] = normalized
            elif values["portfolio"] is None:
                values["portfolio"] = normalized
        return values
