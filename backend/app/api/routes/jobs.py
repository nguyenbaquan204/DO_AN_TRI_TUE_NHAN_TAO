from typing import List
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
import pytesseract

from app.core.database import get_db
from app.core.security import get_current_user, require_recruiter_or_admin
from app.models.analysis_log import AnalysisLog
from app.models.job import Job
from app.models.match import Match
from app.schemas.job import JobCreate, JobOut, JobUpdate
from app.services.jd_parser import JDParser
from app.services.cv_parser import CVParser

router = APIRouter()
MAX_JD_SIZE_BYTES = 5 * 1024 * 1024


@router.get("", response_model=List[JobOut])
def list_jobs(
    db: Session = Depends(get_db),
    current_user=Depends(require_recruiter_or_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    jobs = db.query(Job).offset(skip).limit(limit).all()
    return jobs


@router.post("", response_model=JobOut)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_recruiter_or_admin),
):
    job = Job(**payload.model_dump(), user_id=current_user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobOut)
def update_job(
    job_id: int,
    payload: JobUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_recruiter_or_admin),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    updated_values = payload.model_dump()
    # Match details are persisted snapshots. Re-score existing candidate/job
    # pairs whenever a field that affects scoring changes.
    scoring_fields = {
        "title",
        "description",
        "experience_required",
        "education_required",
        "education_level",
        "required_skills",
        "preferred_skills",
    }
    should_refresh_matches = any(
        getattr(job, field) != updated_values[field] for field in scoring_fields
    )
    candidate_ids = (
        [candidate_id for (candidate_id,) in db.query(Match.candidate_id)
         .filter(Match.job_id == job_id).distinct().all()]
        if should_refresh_matches
        else []
    )
    for field, value in updated_values.items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)

    if candidate_ids:
        # Import locally to avoid coupling route modules during initialization.
        from app.api.routes.matching import create_match

        for candidate_id in candidate_ids:
            create_match(job_id, candidate_id, db, current_user)
        db.refresh(job)
    return job


@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"success": True, "message": "Job deleted"}


@router.post("/{job_id}/analyze")
def analyze_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    analysis = JDParser.analyze(job.description, job.title)
    job.analysis_summary = str(analysis)
    db.add(AnalysisLog(entity_type="job", entity_id=job.id, action="JD analyzed", status="COMPLETED", message="JD analyzed successfully"))
    db.commit()
    return analysis


@router.get("/{job_id}/analysis")
def get_job_analysis(job_id: int, db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    analysis = JDParser.analyze(job.description, job.title)
    return analysis


@router.post("/{job_id}/upload-jd")
def upload_jd(job_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=400, detail="JD must be PDF, DOCX, or TXT")
    contents = file.file.read(MAX_JD_SIZE_BYTES + 1)
    if len(contents) > MAX_JD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="JD exceeds the 5 MB limit")
    if suffix == ".txt":
        text_content = contents.decode("utf-8", errors="replace")
    else:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            handle.write(contents)
            temp_path = handle.name
        try:
            text_content = CVParser.read_file(temp_path)
        except pytesseract.TesseractNotFoundError as exc:
            raise HTTPException(status_code=422, detail="OCR engine is not installed on the server.") from exc
        except pytesseract.TesseractError as exc:
            raise HTTPException(status_code=422, detail="OCR could not read this scan. Check the server's English and Vietnamese OCR data.") from exc
        finally:
            Path(temp_path).unlink(missing_ok=True)
    if not text_content.strip():
        raise HTTPException(status_code=422, detail="No readable text found in the job description.")
    suggestions = JDParser.analyze(text_content, job.title)
    return {"job_id": job_id, "filename": file.filename, "suggestions": suggestions, "applied": False}
