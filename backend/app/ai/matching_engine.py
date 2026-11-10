import logging
import os
import re
import unicodedata
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.skill_taxonomy import SkillTaxonomy

logger = logging.getLogger(__name__)


def _load_sentence_transformer():
    if os.getenv("ENABLE_SENTENCE_TRANSFORMERS", "0").lower() in {"0", "false", "no", "off"}:
        return None
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer
    except Exception as exc:
        logger.warning("Sentence Transformer import failed; using TF-IDF fallback: %s", exc)
        return None


class MatchingEngine:
    """Explainable CV/JD scoring with a multilingual E5 semantic signal.

    E5 is pretrained and used as an embedding model; the final score is still
    the explicit weighted combination of skills, experience, education,
    projects, TF-IDF and semantic similarity.
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv("MODEL_NAME", "intfloat/multilingual-e5-small")
        self.encoder = None
        self.embedding_status = "not-loaded"
        self._encoder_initialized = False

    def _ensure_encoder(self) -> None:
        if self._encoder_initialized:
            return
        self._encoder_initialized = True
        transformer = _load_sentence_transformer()
        if transformer is None:
            self.embedding_status = "tfidf-fallback"
            return
        try:
            self.encoder = transformer(self.model_name)
            self.embedding_status = "sentence-transformer"
        except Exception as exc:
            logger.warning("Embedding model %s failed to load; using TF-IDF fallback: %s", self.model_name, exc)
            self.encoder = None
            self.embedding_status = "tfidf-fallback"

    @staticmethod
    def _similarity(cv_text: str, jd_text: str) -> float:
        if not (cv_text or "").strip() or not (jd_text or "").strip():
            return 0.0
        try:
            # Keep these exact vectorizer settings aligned with the trained
            # classifier's TF-IDF feature so its existing artifact stays valid.
            matrix = TfidfVectorizer(stop_words="english").fit_transform([cv_text, jd_text])
        except ValueError:
            return 0.0
        return float(cosine_similarity(matrix[0], matrix[1])[0][0])

    def tfidf_similarity(self, cv_text: str, jd_text: str) -> float:
        return self._similarity(cv_text, jd_text)

    @staticmethod
    def _chunks(text: str, words_per_chunk: int = 120, max_chunks: int = 24) -> list[str]:
        words = re.findall(r"\S+", text or "")
        if not words:
            return []
        chunks = [" ".join(words[index:index + words_per_chunk]) for index in range(0, len(words), words_per_chunk)]
        if len(chunks) <= max_chunks:
            return chunks
        # Keep the opening context and sample the rest of a long CV/JD evenly.
        indexes = [round(index * (len(chunks) - 1) / (max_chunks - 1)) for index in range(max_chunks)]
        return [chunks[index] for index in indexes]

    def semantic_similarity(self, cv_text: str, jd_text: str) -> float:
        if not (cv_text or "").strip() or not (jd_text or "").strip():
            return 0.0
        self._ensure_encoder()
        if self.encoder is None:
            return 0.0

        cv_chunks = self._chunks(cv_text)
        jd_chunks = self._chunks(jd_text)
        if not cv_chunks or not jd_chunks:
            return 0.0

        is_e5 = "e5" in self.model_name.casefold()
        query_prefix = "query: " if is_e5 else ""
        passage_prefix = "passage: " if is_e5 else ""
        inputs = [query_prefix + chunk for chunk in jd_chunks] + [passage_prefix + chunk for chunk in cv_chunks]
        try:
            embeddings = self.encoder.encode(inputs, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
            query_vectors = embeddings[:len(jd_chunks)]
            cv_vectors = embeddings[len(jd_chunks):]
            pair_scores = cosine_similarity(query_vectors, cv_vectors)
            # A long JD may contain boilerplate. Average the strongest five
            # requirement-to-CV chunk matches rather than truncating the whole file.
            best_for_each_requirement = pair_scores.max(axis=1)
            best = sorted((float(value) for value in best_for_each_requirement), reverse=True)[:5]
            return max(0.0, min(1.0, sum(best) / len(best))) if best else 0.0
        except Exception as exc:
            logger.warning("Embedding comparison failed; using TF-IDF fallback: %s", exc)
            self.encoder = None
            self.embedding_status = "tfidf-fallback"
            return 0.0

    def encode_texts(self, texts: Iterable[str]):
        self._ensure_encoder()
        if self.encoder is None:
            raise RuntimeError("Sentence transformer model is unavailable")
        values = list(texts)
        if "e5" in self.model_name.casefold():
            values = [f"passage: {text}" for text in values]
        return self.encoder.encode(values, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)

    def model_status(self) -> dict:
        return {
            "model_name": self.model_name,
            "model_type": "Multilingual E5 sentence embedding" if "e5" in self.model_name.casefold() else "Sentence Transformer embedding",
            "enabled": os.getenv("ENABLE_SENTENCE_TRANSFORMERS", "0").lower() not in {"0", "false", "no", "off"},
            "status": self.embedding_status,
            "loaded": self.encoder is not None,
            "fallback": "TF-IDF" if self.encoder is None else None,
            "training_mode": "pretrained; not fine-tuned on this project's data",
        }

    @staticmethod
    def _years(text: str) -> float:
        source = text or ""
        years = [float(value.replace(",", ".")) for value in re.findall(r"(\d+(?:[.,]\d+)?)\s*\+?\s*(?:years?|năm)\b", source, re.I)]
        months = [float(value.replace(",", ".")) / 12 for value in re.findall(r"(\d+(?:[.,]\d+)?)\s*\+?\s*(?:months?|mos?|tháng|thang)\b", source, re.I)]
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
            (("bachelor", "cu nhan", "cunhan", "dai hoc", "ky su"), 2),
            (("degree", "cao dang"), 1),
        ]
        # OCR often flattens adjacent fields (for example "Bachelor2 years").
        # Treat adjoining digits as separators while still rejecting partial
        # matches inside ordinary words.
        needed = next((level for terms, level in levels if any(re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", required) for term in terms)), 1)
        actual = next((level for terms, level in levels if any(re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", candidate) for term in terms)), 0)
        return round(min(100.0, actual / needed * 100.0), 2)

    def score_candidate(
        self,
        cv_text: str,
        jd_text: str,
        candidate_skills: Iterable[str],
        required_skills: Iterable[str],
        required_experience_years: float = 0.0,
        education_required: str | None = None,
        *,
        use_semantic: bool = True,
        candidate_experience_years: float | None = None,
        candidate_education: str | None = None,
        candidate_projects: list | None = None,
    ) -> dict:
        required = {SkillTaxonomy.normalize(skill) for skill in required_skills if skill}
        candidate = {SkillTaxonomy.normalize(skill) for skill in candidate_skills if skill}
        matched = sorted(required & candidate)
        missing = sorted(required - candidate)
        additional = sorted(candidate - required)
        skill_score = len(matched) / len(required) * 100 if required else 100.0
        candidate_years = self._years(cv_text) if candidate_experience_years is None else max(0.0, float(candidate_experience_years))
        experience_score = 100.0 if required_experience_years <= 0 else min(100.0, candidate_years / required_experience_years * 100.0)
        education_score = self._education_score(cv_text if candidate_education is None else candidate_education, education_required)
        project_terms = r"\b(?:projects?|dự\s+án|phát\s+triển|triển\s+khai|xây\s+dựng|developed|built|implemented)\b"
        project_score = min(100.0, 100.0 * len(re.findall(project_terms, cv_text or "", re.I)) / 3.0)

        if candidate_projects is not None:
            project_score = min(100.0, len([p for p in candidate_projects if p]) / 3.0 * 100.0)

        tfidf_score = self.tfidf_similarity(cv_text, jd_text) * 100
        semantic_score = self.semantic_similarity(cv_text, jd_text) * 100 if use_semantic else 0.0
        semantic_available = use_semantic and self.encoder is not None and self.embedding_status == "sentence-transformer"
        if semantic_available:
            tfidf_weight, semantic_weight = 0.10, 0.10
            text_score = tfidf_score * tfidf_weight + semantic_score * semantic_weight
            method = "hybrid-e5-tfidf"
        else:
            tfidf_weight, semantic_weight = 0.20, 0.0
            text_score = tfidf_score * tfidf_weight
            method = "tfidf-fallback" if use_semantic else "tfidf-baseline"

        overall = skill_score * 0.40 + text_score + experience_score * 0.15 + education_score * 0.15 + project_score * 0.10
        insufficient = not (cv_text.strip() or candidate or candidate_years or candidate_education or candidate_projects) or not (jd_text.strip() or required or required_experience_years or education_required)
        if insufficient:
            overall = skill_score = experience_score = education_score = project_score = 0.0
        return {
            "data_status": "insufficient-data" if insufficient else "scored",
            "overall_score": round(max(0.0, min(100.0, overall)), 2),
            "skill_score": round(skill_score, 2),
            "experience_score": round(experience_score, 2),
            "education_score": round(education_score, 2),
            "project_score": round(project_score, 2),
            "tfidf_score": round(tfidf_score, 2),
            "semantic_score": round(semantic_score, 2),
            "matched_skills": matched,
            "missing_skills": missing,
            "additional_skills": additional,
            "experience_gap": round(max(0.0, required_experience_years - candidate_years), 2),
            "embedding_status": self.embedding_status,
            "embedding_model": self.model_name if semantic_available else None,
            "scoring_method": method,
            "explanation": [
                "Điểm tổng hợp gồm kỹ năng (40%), văn bản (20%), kinh nghiệm (15%), học vấn (15%) và dự án (10%).",
                "Điểm văn bản chia đều giữa TF-IDF và độ tương đồng ngữ nghĩa khi E5 sẵn sàng; nếu không, hệ thống dùng TF-IDF làm phương án dự phòng.",
                f"Cách tính đang dùng: {method}.",
            ],
        }
