from __future__ import annotations

from pathlib import Path
import hashlib

import pandas as pd

REAL_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "training" / "resume-job-fit-merged-v1" / "data"
LABEL_MAPPING = {"Good Fit": "HIGH", "Potential Fit": "MEDIUM", "No Fit": "LOW"}


def load_real_training_records() -> list[dict]:
    files = sorted(REAL_DATA_DIR.glob("*.parquet"))
    if len(files) != 3:
        raise FileNotFoundError(f"Expected three parquet shards in {REAL_DATA_DIR}")
    frame = pd.concat([pd.read_parquet(path) for path in files], ignore_index=True)
    required = {"resume", "jd", "label", "source", "resume_domain", "jd_domain"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Dataset is missing columns: {sorted(required - set(frame.columns))}")
    frame = frame.fillna("")
    records = []
    for row in frame.itertuples(index=False):
        resume = str(row.resume)
        jd = str(row.jd)
        records.append({
            "candidate_text": resume,
            "job_text": jd,
            "label": LABEL_MAPPING.get(str(row.label), ""),
            "source": str(row.source),
            "resume_domain": str(row.resume_domain),
            "jd_domain": str(row.jd_domain),
            "resume_id": hashlib.sha256(resume.encode("utf-8")).hexdigest(),
            "jd_id": hashlib.sha256(jd.encode("utf-8")).hexdigest(),
        })
    if any(not record["label"] for record in records):
        raise ValueError("Dataset contains an unknown label")
    return records
