from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedGroupKFold

from training.data_loader import load_real_training_records
from training.feature_builder import FEATURE_NAMES, FeatureBuilder, _tfidf_token_counts

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "backend" / "models"
MODEL_PATH = MODEL_DIR / "candidate_job_suitability_model.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"
SPLIT_PATH = ROOT / "data" / "training" / "real_group_split.json"
CLASSES = ["HIGH", "MEDIUM", "LOW"]


def _split_records(records: list[dict]):
    groups = [record["resume_id"] for record in records]
    labels = [record["label"] for record in records]
    splitter = StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=42)
    folds = list(splitter.split(records, labels, groups))
    test_folds = {0, 1, 2}
    validation_folds = {3, 4, 5}
    fold_by_index = {}
    for fold_index, (_, indices) in enumerate(folds):
        for index in indices:
            fold_by_index[index] = fold_index
    train = [index for index in range(len(records)) if fold_by_index[index] not in test_folds | validation_folds]
    validation = [index for index in range(len(records)) if fold_by_index[index] in validation_folds]
    test = [index for index in range(len(records)) if fold_by_index[index] in test_folds]
    return train, validation, test


def _build_matrix(records: list[dict]):
    builder = FeatureBuilder(semantic_enabled=False, cache_text_tokens=True)
    matrix = []
    labels = []
    try:
        for index, record in enumerate(records, start=1):
            features = builder.build_from_texts(record["candidate_text"], record["job_text"])
            matrix.append([features[name] for name in FEATURE_NAMES])
            labels.append(record["label"])
            if index % 5000 == 0:
                print(f"Built features for {index}/{len(records)} records", flush=True)
    finally:
        # Text/token data is only a batch-training optimization; don't keep it
        # alive after the numeric matrix has been constructed.
        _tfidf_token_counts.cache_clear()
    return matrix, labels


def _metrics(y_true, predictions):
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, predictions, labels=CLASSES, zero_division=0
    )
    report = {
        "accuracy": accuracy_score(y_true, predictions),
        "precision_macro": precision.mean(),
        "recall_macro": recall.mean(),
        "f1_macro": f1.mean(),
        "precision_weighted": precision_recall_fscore_support(
            y_true, predictions, average="weighted", zero_division=0
        )[0],
        "recall_weighted": precision_recall_fscore_support(
            y_true, predictions, average="weighted", zero_division=0
        )[1],
        "f1_weighted": precision_recall_fscore_support(
            y_true, predictions, average="weighted", zero_division=0
        )[2],
        "confusion_matrix": confusion_matrix(y_true, predictions, labels=CLASSES).tolist(),
    }
    return report


def train() -> dict:
    records = load_real_training_records()
    train_indices, validation_indices, test_indices = _split_records(records)
    resume_sets = [{records[index]["resume_id"] for index in indices} for indices in (train_indices, validation_indices, test_indices)]
    leakage_free = not (resume_sets[0] & resume_sets[1] or resume_sets[0] & resume_sets[2] or resume_sets[1] & resume_sets[2])
    if not leakage_free:
        raise RuntimeError("Resume leakage detected in group-aware split")

    X, y = _build_matrix(records)
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=2,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    model.fit([X[index] for index in train_indices], [y[index] for index in train_indices])
    validation_predictions = model.predict([X[index] for index in validation_indices])
    test_predictions = model.predict([X[index] for index in test_indices])
    metrics = {
        "validation": _metrics([y[index] for index in validation_indices], validation_predictions),
        "test": _metrics([y[index] for index in test_indices], test_predictions),
    }
    majority = Counter(y[index] for index in train_indices).most_common(1)[0][0]
    metrics["majority_baseline_test"] = _metrics(
        [y[index] for index in test_indices],
        [majority] * len(test_indices),
    )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    split_payload = {
        "random_seed": 42,
        "train_resume_ids": sorted(resume_sets[0]),
        "validation_resume_ids": sorted(resume_sets[1]),
        "test_resume_ids": sorted(resume_sets[2]),
    }
    SPLIT_PATH.write_text(json.dumps(split_payload, indent=2), encoding="utf-8")
    metadata = {
        "model_name": "Candidate-Job Suitability Classifier",
        "model_type": "RandomForestClassifier",
        "model_version": "2.1-real-grouped-boundary-skills",
        "feature_pipeline_version": "2.1-boundary-aware-skill-matching",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "classes": list(model.classes_),
        "feature_names": FEATURE_NAMES,
        "record_count": len(records),
        "unique_resume_count": len({record["resume_id"] for record in records}),
        "unique_jd_count": len({record["jd_id"] for record in records}),
        "split_strategy": "StratifiedGroupKFold by resume_id; original source split ignored",
        "split_record_counts": {"train": len(train_indices), "validation": len(validation_indices), "test": len(test_indices)},
        "split_resume_counts": {"train": len(resume_sets[0]), "validation": len(resume_sets[1]), "test": len(resume_sets[2])},
        "leakage_check": leakage_free,
        "label_mapping": {"Good Fit": "HIGH", "Potential Fit": "MEDIUM", "No Fit": "LOW"},
        "class_distribution": dict(Counter(y)),
        "class_weight": "balanced",
        "semantic_feature": "unavailable; semantic_similarity=0.0 during training",
        "metrics": metrics,
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return metadata


if __name__ == "__main__":
    train()
