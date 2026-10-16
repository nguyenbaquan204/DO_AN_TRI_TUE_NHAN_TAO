from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_recruiter_or_admin
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match import Match
from app.models.resume import Resume

router = APIRouter()


@router.get("/overview")
def overview(db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    total_jobs = db.query(Job).count()
    open_jobs = db.query(Job).filter(Job.status == "open").count()
    total_candidates = db.query(Candidate).count()
    cv_analyzed = db.query(Resume).filter(Resume.analysis_status == "COMPLETED").count()
    total_matches = db.query(Match).count()
    avg_score = db.query(func.avg(Match.overall_score)).scalar() or 0.0
    suitability_counts = {
        label: db.query(Match).filter(Match.predicted_class == label).count()
        for label in ("HIGH", "MEDIUM", "LOW")
    }
    candidates_per_job = [
        {"job_id": job.id, "job_title": job.title, "count": db.query(Match).filter(Match.job_id == job.id).count()}
        for job in db.query(Job).all()
    ]
    cv_processing_status = {
        status: db.query(Resume).filter(Resume.analysis_status == status).count()
        for status in ("PENDING", "PROCESSING", "COMPLETED", "FAILED")
    }
    return {
        "total_jobs": total_jobs,
        "open_jobs": open_jobs,
        "total_candidates": total_candidates,
        "cv_analyzed": cv_analyzed,
        "total_matches": total_matches,
        "average_matching_score": round(avg_score, 2),
        "suitability_distribution": suitability_counts,
        "candidates_per_job": candidates_per_job,
        "cv_processing_status": cv_processing_status,
    }
