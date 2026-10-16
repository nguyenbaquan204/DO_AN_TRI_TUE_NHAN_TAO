import hashlib
import json
import re
import unicodedata
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from threading import Lock

_EXTRACT_CACHE: OrderedDict[bytes, tuple[str, ...]] = OrderedDict()
_EXTRACT_CACHE_MAXSIZE = 1024
_EXTRACT_CACHE_LOCK = Lock()


class SkillExtractor:
    SKILLS_FILE = Path(__file__).resolve().parents[1] / "data" / "skills.json"

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = (text or "").replace("đ", "d").replace("Đ", "D")
        decomposed = unicodedata.normalize("NFKD", text)
        return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()

    @staticmethod
    @lru_cache(maxsize=1)
    def load_skill_map():
        with SkillExtractor.SKILLS_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    @lru_cache(maxsize=1)
    def _skill_patterns():
        return tuple(
            (
                skill_name,
                tuple(
                    re.compile(rf"(?<![a-z0-9+#]){re.escape(SkillExtractor._normalize_text(alias))}(?![a-z0-9+#])")
                    for alias in [skill_name] + aliases
                ),
            )
            for skill_name, aliases in SkillExtractor.load_skill_map().items()
        )

    @staticmethod
    def extract(text: str):
        text = text or ""
        cache_key = hashlib.sha256(text.encode("utf-8")).digest()
        with _EXTRACT_CACHE_LOCK:
            cached = _EXTRACT_CACHE.get(cache_key)
            if cached is not None:
                _EXTRACT_CACHE.move_to_end(cache_key)
                return list(cached)

        normalized = SkillExtractor._normalize_text(text)
        found = tuple(
            sorted(
                skill_name
                for skill_name, patterns in SkillExtractor._skill_patterns()
                if any(pattern.search(normalized) for pattern in patterns)
            )
        )
        with _EXTRACT_CACHE_LOCK:
            _EXTRACT_CACHE[cache_key] = found
            _EXTRACT_CACHE.move_to_end(cache_key)
            if len(_EXTRACT_CACHE) > _EXTRACT_CACHE_MAXSIZE:
                _EXTRACT_CACHE.popitem(last=False)
        return list(found)

    @staticmethod
    def normalize_skills(skills):
        return sorted({str(skill).strip() for skill in (skills or []) if str(skill).strip()})
