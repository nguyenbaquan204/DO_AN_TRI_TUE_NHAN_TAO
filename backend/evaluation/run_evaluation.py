from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ai.matching_engine import MatchingEngine
from app.core.database import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = REPO_ROOT / "data" / "evaluation" / "matches.json"


def load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_pair_text(candidate_id: int, job_id: int) -> tuple[str, str]:
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        job = db.query(Job).filter(Job.id == job_id).first()
        if candidate is None or job is None:
            return "", ""
        return (candidate.raw_text or "", job.description or "")
    finally:
        db.close()


def binary_metrics(prediction_scores: list[float], labels: list[str]) -> dict[str, float]:
    predicted = [1 if score >= 0.5 else 0 for score in prediction_scores]
    expected = [1 if label != "low" else 0 for label in labels]
    tp = sum(1 for p, e in zip(predicted, expected) if p == 1 and e == 1)
    fp = sum(1 for p, e in zip(predicted, expected) if p == 1 and e == 0)
    fn = sum(1 for p, e in zip(predicted, expected) if p == 0 and e == 1)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def tfidf_scores(items: list[dict[str, Any]]) -> list[float]:
    scores: list[float] = []
    for item in items:
        cv_text, jd_text = get_pair_text(item["candidate_id"], item["job_id"])
        if not cv_text or not jd_text:
            scores.append(0.0)
            continue
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform([cv_text, jd_text])
        score = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        scores.append(float(score))
    return scores


def sentence_transformer_scores(items: list[dict[str, Any]], engine: MatchingEngine) -> list[float]:
    if engine.encoder is None:
        return [0.0 for _ in items]
    scores: list[float] = []
    for item in items:
        cv_text, jd_text = get_pair_text(item["candidate_id"], item["job_id"])
        if not cv_text or not jd_text:
            scores.append(0.0)
            continue
        embeddings = engine.encode_texts([cv_text, jd_text])
        score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        scores.append(float(score))
    return scores


def run_evaluation() -> dict[str, dict[str, float] | str]:
    items = load_dataset()
    labels = [item["expected_relevance"] for item in items]
    tfidf_prediction = tfidf_scores(items)
    tfidf_metrics = binary_metrics(tfidf_prediction, labels)

    engine = MatchingEngine()
    if engine.encoder is None:
        semantic_metrics = {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        semantic_status = "unavailable in this environment; TF-IDF fallback used"
    else:
        semantic_prediction = sentence_transformer_scores(items, engine)
        semantic_metrics = binary_metrics(semantic_prediction, labels)
        semantic_status = "available"

    return {
        "tfidf": tfidf_metrics,
        "sentence_transformer": semantic_metrics,
        "sentence_transformer_status": semantic_status,
    }


def main() -> None:
    results = run_evaluation()
    print("Method: TF-IDF")
    print(f"Precision: {results['tfidf']['precision']:.4f}")
    print(f"Recall: {results['tfidf']['recall']:.4f}")
    print(f"F1: {results['tfidf']['f1']:.4f}")
    print()
    print("Method: Sentence Transformer")
    print(f"Status: {results['sentence_transformer_status']}")
    if results["sentence_transformer_status"] == "available":
        print(f"Precision: {results['sentence_transformer']['precision']:.4f}")
        print(f"Recall: {results['sentence_transformer']['recall']:.4f}")
        print(f"F1: {results['sentence_transformer']['f1']:.4f}")
    else:
        print("Precision: unavailable")
        print("Recall: unavailable")
        print("F1: unavailable")


if __name__ == "__main__":
    main()
