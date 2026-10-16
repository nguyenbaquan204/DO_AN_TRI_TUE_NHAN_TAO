import json
from pathlib import Path


DEMO_JOBS_FILE = Path(__file__).resolve().parents[1] / "data" / "demo_jobs.json"


def load_demo_jobs() -> list[dict]:
    with DEMO_JOBS_FILE.open("r", encoding="utf-8") as handle:
        jobs = json.load(handle)
    if len(jobs) != 10 or len({job["department"] for job in jobs}) != 10:
        raise ValueError("Demo data must define exactly ten jobs across ten unique industries")
    return jobs
