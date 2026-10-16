from __future__ import annotations
from typing import Iterable

class EmbeddingProvider:
    status = "unavailable"
    def encode(self, texts: Iterable[str]):
        raise NotImplementedError

class SentenceTransformerProvider(EmbeddingProvider):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.status = "unavailable"
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.status = "sentence-transformer"
        except (ImportError, OSError, RuntimeError):
            self.status = "unavailable"

    def encode(self, texts: Iterable[str]):
        if self.model is None:
            raise RuntimeError("Sentence-transformer model is unavailable; use TF-IDF fallback")
        return self.model.encode(list(texts), convert_to_numpy=True)

class EmbeddingService:
    def __init__(self, provider: EmbeddingProvider):
        self.provider = provider

    @property
    def status(self):
        return self.provider.status

    def encode(self, texts: Iterable[str]):
        return self.provider.encode(texts)
