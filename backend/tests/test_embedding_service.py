from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.matching_engine import MatchingEngine


def test_embedding_service_encodes_text(monkeypatch):
    monkeypatch.setenv("ENABLE_SENTENCE_TRANSFORMERS", "0")
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
    assert engine.embedding_status in {"not-loaded", "sentence-transformer", "tfidf-fallback"}


def test_embedding_service_is_lazy_loaded():
    engine = MatchingEngine()
    assert engine._encoder_initialized is False


def test_e5_similarity_uses_query_and_passage_prefixes_and_chunks_long_text():
    class FakeEncoder:
        def __init__(self):
            self.inputs = []

        def encode(self, texts, **_kwargs):
            self.inputs = list(texts)
            return np.tile(np.array([[1.0, 0.0]]), (len(self.inputs), 1))

    engine = MatchingEngine("intfloat/multilingual-e5-small")
    engine.encoder = FakeEncoder()
    engine.embedding_status = "sentence-transformer"
    engine._encoder_initialized = True
    long_cv = " ".join(f"word{index}" for index in range(400))

    score = engine.semantic_similarity(long_cv, "Mô tả công việc")

    assert score > 0.99
    assert engine.encoder.inputs[0] == "query: Mô tả công việc"
    assert engine.encoder.inputs[1].startswith("passage: ")
    assert len(engine.encoder.inputs) > 2
    assert len(engine._chunks(" ".join(str(index) for index in range(5000)))) <= 24
