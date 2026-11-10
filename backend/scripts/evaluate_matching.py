"""Compare the explainable TF-IDF baseline with the E5 + TF-IDF hybrid."""

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.ai.matching_engine import MatchingEngine
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.match import Match
from app.models.match_detail import MatchDetail
from app.services.matching_inputs import scoring_inputs, SCORING_VERSION
from app.services.jd_parser import JDParser
from app.services.skill_extractor import SkillExtractor


RELEVANCE = {"low": 0, "not_relevant": 0, "irrelevant": 0, "medium": 1, "partially_relevant": 1, "high": 2, "relevant": 2}


def relevance_value(value) -> int:
    if isinstance(value, (int, float)):
        return max(0, min(2, int(value)))
    key = str(value or "").strip().casefold().replace(" ", "_")
    if key not in RELEVANCE:
        raise ValueError(f"Unsupported relevance label: {value!r}; use low/medium/high or 0/1/2")
    return RELEVANCE[key]


def ranking_metrics(records: list[dict], k: int = 5) -> dict:
    grouped = defaultdict(list)
    for record in records:
        grouped[record["job_id"]].append(record)
    if not grouped:
        return {"queries": 0, f"ndcg@{k}": 0.0, f"mrr@{k}": 0.0}

    ndcg_values = []
    mrr_values = []
    for items in grouped.values():
        items.sort(key=lambda item: (-item["score"], item["candidate_id"]))
        ranked = items[:k]
        gains = [2 ** item["relevance"] - 1 for item in ranked]
        dcg = sum(gain / math.log2(position + 2) for position, gain in enumerate(gains))
        ideal = sorted((item["relevance"] for item in items), reverse=True)[:k]
        ideal_dcg = sum((2 ** grade - 1) / math.log2(position + 2) for position, grade in enumerate(ideal))
        ndcg_values.append(dcg / ideal_dcg if ideal_dcg else 0.0)
        first_relevant = next((position for position, item in enumerate(ranked, start=1) if item["relevance"] > 0), None)
        mrr_values.append(1 / first_relevant if first_relevant else 0.0)

    return {
        "queries": len(grouped),
        f"ndcg@{k}": round(sum(ndcg_values) / len(ndcg_values), 4),
        f"mrr@{k}": round(sum(mrr_values) / len(mrr_values), 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=PROJECT_DIR / "data" / "evaluation" / "matches.json")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    if args.k < 1:
        parser.error("--k must be a positive integer")
    if not args.data.exists():
        parser.error(f"Label file not found: {args.data}")

    labels = json.loads(args.data.read_text(encoding="utf-8"))
    if not isinstance(labels, list):
        parser.error("The label file must contain a JSON array")

    db = SessionLocal()
    engine = MatchingEngine(get_settings().model_name)
    baseline, hybrid = [], []
    missing = []
    input_snapshots, methods = [], []
    seen = set()
    candidate_cache, job_cache = {}, {}
    try:
        for row_number, label in enumerate(labels, start=1):
            try:
                candidate_id = int(label["candidate_id"])
                job_id = int(label["job_id"])
                relevance = relevance_value(label.get("expected_relevance", label.get("relevance")))
            except (KeyError, TypeError, ValueError) as exc:
                parser.error(f"Invalid label on row {row_number}: {exc}")

            pair = (candidate_id, job_id)
            if pair in seen:
                parser.error(f"Duplicate pair on row {row_number}: {pair}")
            seen.add(pair)
            if candidate_id not in candidate_cache:
                candidate_cache[candidate_id] = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if job_id not in job_cache:
                job_cache[job_id] = db.query(Job).filter(Job.id == job_id).first()
            candidate = candidate_cache[candidate_id]
            job = job_cache[job_id]
            if candidate is None or job is None:
                missing.append({"row": row_number, "candidate_id": candidate_id, "job_id": job_id})
                continue

            shared = scoring_inputs(candidate, job)
            input_snapshots.append({"candidate_id": candidate_id, "job_id": job_id, "relevance": relevance, "inputs": shared})
            base_score = engine.score_candidate(**shared, use_semantic=False)["overall_score"]
            hybrid_result = engine.score_candidate(**shared, use_semantic=True)
            methods.append(hybrid_result["scoring_method"])
            hybrid_score = hybrid_result["overall_score"]
            baseline.append({"job_id": job_id, "candidate_id": candidate_id, "relevance": relevance, "score": base_score})
            hybrid.append({"job_id": job_id, "candidate_id": candidate_id, "relevance": relevance, "score": hybrid_score})
    finally:
        db.close()

    if missing or not baseline:
        parser.error(f"Evaluation requires all labeled pairs to exist; missing={missing}, usable={len(baseline)}")
    comparison_valid = all(method == "hybrid-e5-tfidf" for method in methods)
    report = {
        "scoring_version": SCORING_VERSION,
        "input_sha256": hashlib.sha256(json.dumps(input_snapshots, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        "semantic_comparison_valid": comparison_valid,
        "actual_methods": sorted(set(methods)),
        "label_file": str(args.data),
        "labeled_pairs_used": len(baseline),
        "missing_database_pairs": missing,
        "embedding": engine.model_status(),
        "metrics": {
            "tfidf_baseline": ranking_metrics(baseline, args.k),
            "e5_tfidf_hybrid": ranking_metrics(hybrid, args.k) if comparison_valid else None,
        },
        "warning": "Metrics are only meaningful if relevance labels were independently judged by humans. Do not report demo or model-generated labels as a validated benchmark.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
