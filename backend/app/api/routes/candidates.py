from typing import List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import require_recruiter_or_admin
from app.models.candidate import Candidate
from app.models.match import Match
from app.models.match_detail import MatchDetail
from app.models.resume import Resume

router = APIRouter()


@router.get("", response_model=List[dict])
def list_candidates(search: str | None = Query(None), analysis_status: str | None = Query(None), db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    candidates = db.query(Candidate).all()
    if search:
        needle = search.lower()
        candidates = [c for c in candidates if needle in (c.full_name or "").lower() or needle in (c.email or "").lower()]
    if analysis_status:
        candidates = [c for c in candidates if c.analysis_status == analysis_status]
    return [{
        "id": c.id,
        "full_name": c.full_name,
        "email": c.email,
        "phone": c.phone,
        "location": c.location,
        "linkedin": c.linkedin,
        "github": c.github,
        "portfolio": c.portfolio,
        "skills": c.skills or [],
        "experience_years": c.experience_years,
        "analysis_status": c.analysis_status,
    } for c in candidates]


@router.get("/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return {
        "id": candidate.id,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "linkedin": candidate.linkedin,
        "github": candidate.github,
        "portfolio": candidate.portfolio,
        "raw_text": candidate.raw_text,
        "skills": candidate.skills or [],
        "experience_years": candidate.experience_years or 0,
        "education": candidate.education or {},
        "work_experience": candidate.work_experience or {},
        "projects": candidate.projects or [],
        "certificates": candidate.certificates or [],
        "languages": candidate.languages or [],
        "analysis_status": candidate.analysis_status,
    }


@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: int, db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    resumes = db.query(Resume).filter(Resume.candidate_id == candidate_id).all()
    resume_paths = [Path(resume.file_path) for resume in resumes if resume.file_path]
    matches = db.query(Match).filter(Match.candidate_id == candidate_id).all()
    match_ids = [match.id for match in matches]

    if match_ids:
        db.query(MatchDetail).filter(MatchDetail.match_id.in_(match_ids)).delete(synchronize_session=False)
        db.query(Match).filter(Match.id.in_(match_ids)).delete(synchronize_session=False)
    db.query(Resume).filter(Resume.candidate_id == candidate_id).delete(synchronize_session=False)
    db.delete(candidate)
    db.commit()

    # Only remove files stored in the application's CV upload directory.
    uploads_dir = Path(get_settings().upload_dir).resolve()
    for file_path in resume_paths:
        try:
            resolved_path = file_path.resolve()
            if resolved_path.is_relative_to(uploads_dir):
                resolved_path.unlink(missing_ok=True)
        except OSError:
            # Keep the database deletion successful if a stale file cannot be removed.
            continue

    return {"success": True, "message": "Candidate and related records deleted"}
