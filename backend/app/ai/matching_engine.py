import os
import re
import logging
import unicodedata
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.skill_taxonomy import SkillTaxonomy

logger = logging.getLogger(__name__)


def _load_sentence_transformer():
    if os.getenv("ENABLE_SENTENCE_TRANSFORMERS", "0").lower() in {"0", "false", "no"}:
        return None
    try:
        from sentence_transformers import SentenceTransformer as provider
        return provider
    except Exception as exc:
        logger.warning("Sentence Transformer import failed; using TF-IDF fallback: %s", exc)
        return None


class MatchingEngine:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.encoder = None
        self.embedding_status = "tfidf-fallback"
        self._encoder_initialized = False

    def _ensure_encoder(self) -> None:
        if self._encoder_initialized:
            return
        self._encoder_initialized = True
        transformer = _load_sentence_transformer()
        if transformer is None:
            return
        try:
            self.encoder = transformer(self.model_name)
            self.embedding_status = "sentence-transformer"
        except Exception as exc:
            logger.warning("Sentence Transformer model failed to load; using TF-IDF fallback: %s", exc)
            self.encoder = None
            self.embedding_status = "tfidf-fallback"

    @staticmethod
    def _similarity(cv_text: str, jd_text: str) -> float:
        if not (cv_text or '').strip() or not (jd_text or '').strip():
            return 0.0
        try:
            matrix = TfidfVectorizer(stop_words="english").fit_transform([cv_text, jd_text])
        except ValueError:
            return 0.0
        return float(cosine_similarity(matrix[0], matrix[1])[0][0])

    def tfidf_similarity(self, cv_text: str, jd_text: str) -> float:
        return self._similarity(cv_text, jd_text)

    def semantic_similarity(self, cv_text: str, jd_text: str) -> float:
        self._ensure_encoder()
        if self.encoder is None:
            return 0.0
        if not (cv_text or '').strip() or not (jd_text or '').strip():
            return 0.0
        embeddings = self.encoder.encode([cv_text, jd_text], convert_to_numpy=True)
        return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])

    def encode_texts(self, texts: Iterable[str]):
        self._ensure_encoder()
        if self.encoder is None:
            raise RuntimeError("Sentence transformer model is unavailable")
        return self.encoder.encode(list(texts), convert_to_numpy=True)

    @staticmethod
    def _years(text: str) -> float:
        source = text or ""
        years = [float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|năm)\b", source, re.I)]
        months = [float(value) / 12 for value in re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:months?|mos?|tháng|thang)\b", source, re.I)]
        return max(years + months, default=0.0)

    @staticmethod
    def _fold_vietnamese(text: str) -> str:
        source = (text or "").replace("đ", "d").replace("Đ", "D")
        return "".join(char for char in unicodedata.normalize("NFKD", source) if not unicodedata.combining(char)).casefold()

    @staticmethod
    def _education_score(cv_text: str, education_required: str | None) -> float:
        if not education_required:
            return 100.0
        required = MatchingEngine._fold_vietnamese(education_required)
        candidate = MatchingEngine._fold_vietnamese(cv_text)
        levels = [
            (("phd", "doctor", "tien si"), 4),
            (("master", "thac si"), 3),
            (("bachelor", "cu nhan", "cunhan"), 2),
            (("degree", "cao dang"), 1),
        ]
        needed = next((level for terms, level in levels if any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", required) for term in terms)), 1)
        actual = next((level for terms, level in levels if any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", candidate) for term in terms)), 0)
        return round(min(100.0, actual / needed * 100.0), 2)

    def score_candidate(self, cv_text: str, jd_text: str, candidate_skills: Iterable[str], required_skills: Iterable[str], required_experience_years: float = 0.0, education_required: str | None = None) -> dict:
        required = {SkillTaxonomy.normalize(skill) for skill in required_skills if skill}
        candidate = {SkillTaxonomy.normalize(skill) for skill in candidate_skills if skill}
        matched = sorted(required & candidate)
        missing = sorted(required - candidate)
        additional = sorted(candidate - required)
        skill_score = len(matched) / len(required) * 100 if required else 100.0
        candidate_years = self._years(cv_text)
        experience_score = 100.0 if required_experience_years <= 0 else min(100.0, candidate_years / required_experience_years * 100.0)
        education_score = self._education_score(cv_text, education_required)
        project_score = min(100.0, 100.0 * len(re.findall(r"\b(project|developed|built|implemented)\b", cv_text or "", re.I)) / 3.0)
        tfidf_score = self.tfidf_similarity(cv_text, jd_text) * 100
        semantic_score = self.semantic_similarity(cv_text, jd_text) * 100
        semantic_available = self.embedding_status == "sentence-transformer"
        tfidf_weight = 0.10 if semantic_available else 0.20
        semantic_weight = 0.10 if semantic_available else 0.0
        overall = (skill_score * 0.40 + tfidf_score * tfidf_weight + semantic_score * semantic_weight + experience_score * 0.15 + education_score * 0.15 + project_score * 0.10)
        return {
            "overall_score": round(max(0.0, min(100.0, overall)), 2),
            "skill_score": round(skill_score, 2), "experience_score": round(experience_score, 2),
            "education_score": round(education_score, 2), "project_score": round(project_score, 2),
            "semantic_score": round(semantic_score, 2), "matched_skills": matched, "missing_skills": missing,
            "additional_skills": additional, "experience_gap": round(max(0.0, required_experience_years - candidate_years), 2),
            "embedding_status": self.embedding_status,
            "explanation": ["Scores use extracted skills, experience, education, projects, and text similarity.", f"Embedding provider: {self.embedding_status}."]
        }
