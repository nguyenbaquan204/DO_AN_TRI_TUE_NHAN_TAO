from __future__ import annotations

import re
import unicodedata
from collections import Counter
from functools import lru_cache
from math import log, sqrt
from pathlib import Path
from typing import Iterable

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from app.ai.matching_engine import MatchingEngine
from app.services.skill_taxonomy import SkillTaxonomy
from app.services.skill_extractor import SkillExtractor

FEATURE_NAMES = [
    "required_skill_match_ratio",
    "preferred_skill_match_ratio",
    "required_skill_matched_count",
    "required_skill_missing_count",
    "preferred_skill_matched_count",
    "candidate_experience_years",
    "required_experience_years",
    "experience_gap",
    "experience_match_ratio",
    "education_level_match",
    "project_relevance",
    "tfidf_similarity",
    "semantic_similarity",
]

_TOKEN_PATTERN = re.compile(r"(?u)\b\w\w+\b")
_YEARS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(years?|năm|months?|mos?|tháng|thang)\b", re.I)
_PROJECT_PATTERN = re.compile(r"\b(project|developed|built|implemented)\b", re.I)


@lru_cache(maxsize=2048)
def _tfidf_token_counts(text: str) -> tuple[tuple[str, int], ...]:
    counts = Counter(
        token for token in _TOKEN_PATTERN.findall(text.lower())
        if token not in ENGLISH_STOP_WORDS
    )
    return tuple(counts.items())


def _normalise_skills(skills: Iterable[str]) -> set[str]:
    return {SkillTaxonomy.normalize(skill) for skill in skills if skill}


def _years(text: str) -> float:
    values = _YEARS_PATTERN.findall(text or "")
    durations = [float(value) / 12 if unit.casefold() in {"month", "months", "mo", "mos", "tháng", "thang"} else float(value) for value, unit in values]
    return max(durations, default=0.0)


def _fold_vietnamese(text: str) -> str:
    source = (text or "").replace("đ", "d").replace("Đ", "D")
    return "".join(char for char in unicodedata.normalize("NFKD", source) if not unicodedata.combining(char)).casefold()


def _education_match(candidate_text: str, required: str | None) -> float:
    if not required:
        return 1.0
    required_lower = _fold_vietnamese(required)
    candidate_lower = _fold_vietnamese(candidate_text)
    levels = [
        (("phd", "doctor", "tien si"), 4),
        (("master", "thac si"), 3),
        (("bachelor", "cu nhan", "cunhan"), 2),
        (("degree", "cao dang"), 1),
    ]
    needed = next((value for terms, value in levels if any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", required_lower) for term in terms)), 1)
    actual = next((value for terms, value in levels if any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", candidate_lower) for term in terms)), 0)
    return 1.0 if actual >= needed else 0.0


def _tfidf_similarity(candidate_text: str, job_text: str, cache_tokens: bool = False) -> float:
    if not candidate_text.strip() or not job_text.strip():
        return 0.0
    if cache_tokens:
        candidate_counts = dict(_tfidf_token_counts(candidate_text))
        job_counts = dict(_tfidf_token_counts(job_text))
    else:
        candidate_counts = Counter(
            token for token in _TOKEN_PATTERN.findall(candidate_text.lower())
            if token not in ENGLISH_STOP_WORDS
        )
        job_counts = Counter(
            token for token in _TOKEN_PATTERN.findall(job_text.lower())
            if token not in ENGLISH_STOP_WORDS
        )
    if not candidate_counts or not job_counts:
        return 0.0
    shared_tokens = candidate_counts.keys() & job_counts.keys()
    unique_idf = log(3 / 2) + 1
    dot_product = sum(candidate_counts[token] * job_counts[token] for token in shared_tokens)
    candidate_norm = sum(
        (count * (1.0 if token in job_counts else unique_idf)) ** 2
        for token, count in candidate_counts.items()
    )
    job_norm = sum(
        (count * (1.0 if token in candidate_counts else unique_idf)) ** 2
        for token, count in job_counts.items()
    )
    if not dot_product or not candidate_norm or not job_norm:
        return 0.0
    return float(dot_product / sqrt(candidate_norm * job_norm))


class FeatureBuilder:
    """Builds the same numeric feature vector for training and inference."""

    def __init__(self, matching_engine: MatchingEngine | None = None, semantic_enabled: bool = True, cache_text_tokens: bool = False):
        self.matching_engine = matching_engine or MatchingEngine()
        self.semantic_enabled = semantic_enabled
        self.cache_text_tokens = cache_text_tokens

    def build(
        self,
        candidate_text: str,
        job_text: str,
        candidate_skills: Iterable[str],
        required_skills: Iterable[str],
        preferred_skills: Iterable[str] = (),
        required_experience_years: float = 0.0,
        education_required: str | None = None,
    ) -> dict[str, float]:
        candidate = _normalise_skills(candidate_skills)
        required = _normalise_skills(required_skills)
        preferred = _normalise_skills(preferred_skills)
        required_matched = candidate & required
        preferred_matched = candidate & preferred
        candidate_years = _years(candidate_text)
        experience_gap = max(0.0, required_experience_years - candidate_years)
        experience_ratio = 1.0 if required_experience_years <= 0 else min(1.0, candidate_years / required_experience_years)
        project_relevance = min(1.0, len(_PROJECT_PATTERN.findall(candidate_text or "")) / 3.0)
        semantic = 0.0
        if self.semantic_enabled:
            self.matching_engine._ensure_encoder()
        if self.semantic_enabled and self.matching_engine.encoder is not None:
            semantic = self.matching_engine.semantic_similarity(candidate_text, job_text)
        values = {
            "required_skill_match_ratio": len(required_matched) / len(required) if required else 1.0,
            "preferred_skill_match_ratio": len(preferred_matched) / len(preferred) if preferred else 1.0,
            "required_skill_matched_count": float(len(required_matched)),
            "required_skill_missing_count": float(len(required - candidate)),
            "preferred_skill_matched_count": float(len(preferred_matched)),
            "candidate_experience_years": candidate_years,
            "required_experience_years": float(required_experience_years),
            "experience_gap": experience_gap,
            "experience_match_ratio": experience_ratio,
            "education_level_match": _education_match(candidate_text, education_required),
            "project_relevance": project_relevance,
            "tfidf_similarity": _tfidf_similarity(candidate_text, job_text, self.cache_text_tokens),
            "semantic_similarity": semantic,
        }
        return values

    def build_from_texts(self, candidate_text: str, job_text: str) -> dict[str, float]:
        """Derive unstructured dataset fields using the same production builder."""
        required_skills = SkillExtractor.extract(job_text)
        candidate_skills = SkillExtractor.extract(candidate_text)
        education_required = next(
            (term for term in ("PhD", "Master", "Bachelor", "degree")
             if term.lower() in job_text.lower()),
            None,
        )
        return self.build(
            candidate_text,
            job_text,
            candidate_skills,
            required_skills,
            preferred_skills=(),
            required_experience_years=_years(job_text),
            education_required=education_required,
        )

    @staticmethod
    def vector(features: dict[str, float]):
        return [[features[name] for name in FEATURE_NAMES]]
