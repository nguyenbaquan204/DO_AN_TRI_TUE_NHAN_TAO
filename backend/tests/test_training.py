import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training.data_loader import load_real_training_records
from training.feature_builder import FEATURE_NAMES, FeatureBuilder
from training.predict import SuitabilityPredictor


def test_training_dataset_has_valid_labels():
    records = load_real_training_records()
    assert len(records) == 93733
    assert {record["label"] for record in records} == {"HIGH", "MEDIUM", "LOW"}


def test_feature_builder_returns_all_numeric_features():
    features = FeatureBuilder().build(
        "Java Spring Boot MySQL Docker 3 years Bachelor built project",
        "Java Spring Boot MySQL Docker 2 years Bachelor",
        ["Java", "Spring Boot", "MySQL", "Docker"],
        ["Java", "Spring Boot", "MySQL", "Docker"],
        ["Git"],
        2,
        "Bachelor",
    )
    assert set(features) == set(FEATURE_NAMES)
    assert all(isinstance(value, float) for value in features.values())


@pytest.mark.parametrize(
    ("candidate", "job"),
    [
        ("Java Spring Boot MySQL", "Java Spring Boot MySQL"),
        ("Python API data service", "Python API database service"),
        ("the and for", "the and for"),
        ("", "Python backend developer"),
    ],
)
def test_fast_tfidf_similarity_matches_sklearn(candidate, job):
    from app.ai.matching_engine import MatchingEngine
    from training.feature_builder import _tfidf_similarity

    cached = _tfidf_similarity(candidate, job, cache_tokens=True)
    uncached = _tfidf_similarity(candidate, job)
    assert cached == pytest.approx(uncached, abs=1e-12)
    assert uncached == pytest.approx(
        MatchingEngine._similarity(candidate, job), abs=1e-12
    )


def test_trained_model_loads_and_predicts():
    predictor = SuitabilityPredictor()
    assert predictor.available
    result = predictor.predict(
        "Java Spring Boot MySQL Docker 3 years Bachelor built backend project",
        "Java Spring Boot MySQL Docker 2 years Bachelor",
        ["Java", "Spring Boot", "MySQL", "Docker"],
        [],
        2,
        "Bachelor",
    )
    assert result["predicted_class"] in {"HIGH", "MEDIUM", "LOW"}
    assert 0.0 <= result["model_confidence"] <= 1.0


def test_trained_model_responds_to_different_features():
    predictor = SuitabilityPredictor()
    strong = predictor.predict(
        "Java Spring Boot MySQL Docker 3 years Bachelor built backend project",
        "Java Spring Boot MySQL Docker 2 years Bachelor",
        ["Java", "Spring Boot", "MySQL", "Docker"],
        [],
        2,
        "Bachelor",
    )
    weak = predictor.predict(
        "React Node.js 1 year Bachelor built frontend project",
        "Java Spring Boot MySQL Docker 2 years Bachelor",
        ["Java", "Spring Boot", "MySQL", "Docker"],
        [],
        2,
        "Bachelor",
    )
    assert strong["predicted_class"] != weak["predicted_class"] or strong["model_confidence"] != weak["model_confidence"]
