from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.matching_engine import MatchingEngine


def test_embedding_service_encodes_text():
    engine = MatchingEngine()
    if engine.embedding_status == "sentence-transformer":
        embeddings = engine.encode_texts(["Java backend developer", "Java backend engineer"])
        assert len(embeddings) == 2
    else:
        try:
            engine.encode_texts(["Java backend developer", "Java backend engineer"])
        except RuntimeError as exc:
            assert "unavailable" in str(exc).lower()
        else:
            raise AssertionError("Fallback must not fabricate embeddings")


def test_embedding_service_same_text_similarity_is_high():
    engine = MatchingEngine()
    if engine.encoder is None:
        assert engine.tfidf_similarity("Java Spring Boot backend developer", "Java Spring Boot backend developer") > 0.9
    else:
        score = engine.semantic_similarity("Java Spring Boot backend developer", "Java Spring Boot backend developer")
        assert score > 0.8


def test_embedding_service_unrelated_text_similarity_is_low():
    engine = MatchingEngine()
    score = engine.semantic_similarity("Java Spring Boot backend developer", "React UI designer") if engine.encoder else engine.tfidf_similarity("Java Spring Boot backend developer", "React UI designer")
    assert score < 0.7


def test_embedding_service_status_is_explicit():
    engine = MatchingEngine()
    assert engine.embedding_status in {"sentence-transformer", "tfidf-fallback"}


def test_embedding_service_is_lazy_loaded():
    engine = MatchingEngine()
    assert engine._encoder_initialized is False
