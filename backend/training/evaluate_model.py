from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib

from training.data_loader import load_real_training_records
from training.train_model import (
    CLASSES,
    MODEL_PATH,
    SPLIT_PATH,
    _build_matrix,
    _metrics,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "data" / "training" / "evaluation_report.json"
REPORT_MD = ROOT / "data" / "training" / "evaluation_report.md"


def main() -> None:
    if not MODEL_PATH.exists() or not SPLIT_PATH.exists():
        raise SystemExit("Run python backend/training/train_model.py first.")
    records = load_real_training_records()
    split = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    test_resume_ids = set(split["test_resume_ids"])
    test_indices = [index for index, record in enumerate(records) if record["resume_id"] in test_resume_ids]
    if not test_indices:
        raise SystemExit("Saved test split contains no records.")
    train_resume_ids = set(split["train_resume_ids"])
    train_labels = [record["label"] for record in records if record["resume_id"] in train_resume_ids]
    majority_label = Counter(train_labels).most_common(1)[0][0]
    # Only the held-out rows are needed for evaluation. Building features for
    # all 93k pairs made this report needlessly slow.
    test_records = [records[index] for index in test_indices]
    X, y = _build_matrix(test_records)
    model = joblib.load(MODEL_PATH)
    predictions = model.predict(X)
    metrics = _metrics(y, predictions)
    report = {
        "dataset_size": len(records),
        "unique_resumes": len({record["resume_id"] for record in records}),
        "unique_jds": len({record["jd_id"] for record in records}),
        "label_distribution": {label: y.count(label) for label in CLASSES},
        "train_size": len([record for record in records if record["resume_id"] in set(split["train_resume_ids"])]),
        "validation_size": len([record for record in records if record["resume_id"] in set(split["validation_resume_ids"])]),
        "test_size": len(test_indices),
        "model": "RandomForestClassifier",
        "features": __import__("training.feature_builder", fromlist=["FEATURE_NAMES"]).FEATURE_NAMES,
        "class_weight": "balanced",
        "semantic_feature": "unavailable; semantic_similarity=0.0",
        "metrics": metrics,
        "majority_baseline_test": _metrics(
            y, [majority_label] * len(test_indices)
        ),
        "limitations": [
            "Dataset contains generated and synthetic records and is not an independently human-labelled benchmark.",
            "Evaluation is grouped by resume, but repeated JD text can occur across splits.",
            "Semantic model was unavailable and was not used.",
            "Do not use these results to justify automated hiring decisions.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [
        "# Real Dataset Evaluation",
        f"- Dataset size: {report['dataset_size']}",
        f"- Unique resumes: {report['unique_resumes']}",
        f"- Unique JDs: {report['unique_jds']}",
        f"- Label distribution: {report['label_distribution']}",
        f"- Train / validation / test records: {report['train_size']} / {report['validation_size']} / {report['test_size']}",
        "- Split: group-aware by resume, seed 42; original source split was not used for evaluation.",
        "- Model: RandomForestClassifier(class_weight='balanced', random_state=42)",
        f"- Features: {', '.join(report['features'])}",
        "",
        "## Test metrics",
    ]
    for key in ("accuracy", "precision_macro", "recall_macro", "f1_macro", "precision_weighted", "recall_weighted", "f1_weighted"):
        md.append(f"- {key}: {report['metrics'][key]:.6f}")
    md.append(f"- majority_baseline_accuracy: {report['majority_baseline_test']['accuracy']:.6f}")
    md.extend(["", "Model accuracy should be compared with the majority-class baseline because the dataset is imbalanced."])
    md.extend(["", "## Confusion matrix (HIGH, MEDIUM, LOW)", "```text"])
    md.extend(str(row) for row in report["metrics"]["confusion_matrix"])
    md.extend(["```", "", "## Limitations", *[f"- {item}" for item in report["limitations"]]])
    REPORT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Accuracy: {report['metrics']['accuracy']:.6f}")
    print(f"Precision (macro): {report['metrics']['precision_macro']:.6f}")
    print(f"Recall (macro): {report['metrics']['recall_macro']:.6f}")
    print(f"F1 (macro): {report['metrics']['f1_macro']:.6f}")
    print(f"F1 (weighted): {report['metrics']['f1_weighted']:.6f}")
    print("Confusion matrix (HIGH, MEDIUM, LOW):")
    for row in report["metrics"]["confusion_matrix"]:
        print(row)


if __name__ == "__main__":
    main()
