"""Frozen evaluation pairs with human labels; no automatic relevance labels."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, JSON, String
from sqlalchemy.orm import Session
from app.core.database import Base, get_db
from app.core.security import require_recruiter_or_admin
from app.models.candidate import Candidate
from app.models.job import Job
from app.api.routes.matching import engine
from app.services.matching_inputs import scoring_inputs, SCORING_VERSION
from scripts.evaluate_matching import ranking_metrics

def label_source(p):
    return 'ai-proposed' if (p.notes or '').startswith('[AI đề xuất;') else ('human' if p.reviewer_id is not None else 'unreviewed')

router = APIRouter()
class EvaluationPair(Base):
    __tablename__ = "evaluation_pairs"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, nullable=False)
    job_id = Column(Integer, nullable=False)
    candidate_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    inputs = Column(JSON, nullable=False)
    relevance = Column(Integer, nullable=True)
    notes = Column(String(2000), default="")
    reviewer_id = Column(Integer, nullable=True)
    reviewed_at = Column(String(50), nullable=True)

class Label(BaseModel):
    relevance: int = Field(ge=0, le=2)
    notes: str = Field(min_length=3, max_length=2000)

@router.post("/prepare")
def prepare(db: Session = Depends(get_db), user=Depends(require_recruiter_or_admin)):
    if db.query(EvaluationPair).count():
        return {"created": 0, "message": "Bộ đánh giá đã tồn tại; các nhãn được giữ nguyên."}
    jobs = db.query(Job).filter(Job.status == "open").order_by(Job.id).limit(10).all()
    candidates = db.query(Candidate).order_by(Candidate.id).limit(20).all()
    for job in jobs:
        for candidate in candidates:
            db.add(EvaluationPair(candidate_id=candidate.id, job_id=job.id,
                candidate_name=candidate.full_name, job_title=job.title,
                inputs=scoring_inputs(candidate, job)))
    db.commit()
    return {"created": len(jobs)*len(candidates)}

@router.get("/pairs")
def pairs(db: Session = Depends(get_db), user=Depends(require_recruiter_or_admin)):
    return [{"id": p.id, "job_id": p.job_id, "candidate_id": p.candidate_id,
             "candidate_name": p.candidate_name, "job_title": p.job_title,
             "inputs": p.inputs, "relevance": p.relevance, "notes": p.notes,
             "label_source": label_source(p), "reviewer_id": p.reviewer_id, "reviewed_at": p.reviewed_at}
            for p in db.query(EvaluationPair).order_by(EvaluationPair.job_id, EvaluationPair.id).all()]

@router.put("/pairs/{pair_id}")
def label(pair_id: int, payload: Label, db: Session = Depends(get_db), user=Depends(require_recruiter_or_admin)):
    p = db.get(EvaluationPair, pair_id)
    if p is None: raise HTTPException(404, "Không tìm thấy cặp đánh giá")
    if len(payload.notes.strip()) < 3: raise HTTPException(422, "Hãy ghi lý do đánh giá")
    if payload.notes.strip().startswith('[AI đề xuất;'):
        raise HTTPException(422, "Hãy đọc lại, sửa lý do và bỏ tiền tố AI trước khi xác nhận nhãn của bạn.")
    p.relevance, p.notes = payload.relevance, payload.notes.strip()
    p.reviewer_id, p.reviewed_at = user.id, datetime.now(timezone.utc).isoformat()
    db.commit()
    return {"saved": True}

@router.post("/run/{job_id}")
def run(job_id: int, db: Session = Depends(get_db), user=Depends(require_recruiter_or_admin)):
    rows = db.query(EvaluationPair).filter(EvaluationPair.job_id == job_id).order_by(EvaluationPair.candidate_id).all()
    if len(rows) < 5 or any(p.relevance is None for p in rows):
        raise HTTPException(422, "Cần ít nhất 5 cặp và gán nhãn toàn bộ ứng viên của vị trí trước khi so sánh.")
    if not any(p.relevance > 0 for p in rows):
        raise HTTPException(422, "Vị trí chưa có hồ sơ phù hợp trong bộ nhãn; cần bổ sung bộ dữ liệu trước khi đánh giá xếp hạng.")
    baseline, hybrid, details = [], [], []
    valid = True
    for p in rows:
        base = engine.score_candidate(**p.inputs, use_semantic=False)
        sem = engine.score_candidate(**p.inputs, use_semantic=True)
        valid = valid and sem["scoring_method"] == "hybrid-e5-tfidf"
        common = {"job_id": job_id, "candidate_id": p.candidate_id, "relevance": p.relevance}
        baseline.append({**common, "score": base["overall_score"]})
        hybrid.append({**common, "score": sem["overall_score"]})
        details.append({**common, "candidate_name": p.candidate_name, "tfidf": base["overall_score"],
                        "hybrid": sem["overall_score"], "missing_skills": sem["missing_skills"]})
    return {"independent_human_benchmark": all(label_source(p) == "human" for p in rows), "scoring_version": SCORING_VERSION, "job_id": job_id,
            "tfidf": ranking_metrics(baseline), "hybrid": ranking_metrics(hybrid) if valid else None,
            "semantic_comparison_valid": valid, "model": engine.model_status(),
            "details": sorted(details, key=lambda r: (-r["hybrid"], r["candidate_id"])),
            "labels": [{"pair_id": p.id, "relevance": p.relevance, "notes": p.notes,
                        "label_source": label_source(p), "reviewer_id": p.reviewer_id, "reviewed_at": p.reviewed_at, "inputs": p.inputs} for p in rows]}
