import json
import re
from pathlib import Path

from app.services.skill_extractor import SkillExtractor


class JDParser:
    SKILLS_FILE = Path(__file__).resolve().parents[1] / "data" / "skills.json"

    @staticmethod
    def load_skills():
        with JDParser.SKILLS_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def extract_title(text: str) -> str:
        patterns = [
            r"(?i)job title\s*[:\-]?\s*([A-Za-z0-9 /&+.-]+)",
            r"(?i)position\s*[:\-]?\s*([A-Za-z0-9 /&+.-]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return "Position"

    @staticmethod
    def extract_required_skills(text: str):
        return SkillExtractor.extract(text)

    @staticmethod
    def extract_experience_years(text: str):
        match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", text, re.I)
        if match:
            return float(match.group(1))
        match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*year", text, re.I)
        if match:
            return float(match.group(1))
        return 0.0

    @staticmethod
    def extract_education(text: str):
        for keyword in ["computer science", "information technology", "software engineering", "computer engineering", "bachelor", "master"]:
            if keyword.lower() in text.lower():
                return keyword.title()
        return None

    @staticmethod
    def _extract_section(text: str, headings: list[str]) -> list[str]:
        pattern = r"(?:" + "|".join(re.escape(h) for h in headings) + r")\s*[:\-]?\s*(.*?)(?=\b(?:responsibilities|qualifications|requirements|preferred|nice to have|education|experience)\b|$)"
        match = re.search(pattern, text, re.I)
        if not match:
            return []
        return [item.strip(" -?") for item in re.split(r"[\n;]|(?<=[.!?])\s+", match.group(1)) if item.strip(" -?")]

    @staticmethod
    def _extract_languages(text: str) -> list[str]:
        return [language for language in ("English", "Vietnamese", "French", "German", "Japanese", "Korean") if re.search(r"\b" + language + r"\b", text, re.I)]

    @staticmethod
    def analyze(text: str, job_title: str | None = None):
        cleaned_text = re.sub(r"\s+", " ", text or "").strip()
        title = job_title or JDParser.extract_title(cleaned_text)
        preferred_section = re.search(
            r"\b(?:preferred(?:\s+qualifications?)?|nice to have|good to have)\s*[:\-]?(.+?)(?=\b(?:responsibilities|qualifications|required|requirements|experience|education)\b|$)",
            cleaned_text,
            re.I,
        )
        required_text = cleaned_text
        preferred_text = ""
        if preferred_section:
            required_text = cleaned_text[:preferred_section.start()] + cleaned_text[preferred_section.end():]
            preferred_text = preferred_section.group(1)
        required = JDParser.extract_required_skills(required_text)
        preferred = JDParser.extract_required_skills(preferred_text)
        return {
            "job_title": title,
            "required_skills": required,
            "preferred_skills": preferred,
            "experience_years": JDParser.extract_experience_years(cleaned_text),
            "education_required": JDParser.extract_education(cleaned_text),
            "responsibilities": JDParser._extract_section(cleaned_text, ["responsibilities", "what you will do"]),
            "qualifications": JDParser._extract_section(cleaned_text, ["qualifications", "requirements", "what you bring"]),
            "languages": JDParser._extract_languages(cleaned_text),
        }
