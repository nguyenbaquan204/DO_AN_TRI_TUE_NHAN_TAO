from typing import List
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
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
from app.services.jd_web_importer import fetch_job_page, looks_like_job_listing

router = APIRouter()
MAX_JD_SIZE_BYTES = 5 * 1024 * 1024


class JDUrlImportRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=2048)


class JDTextImportRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=60_000)
    title: str | None = Field(None, max_length=255)


def _add_jd_suggestions(page: dict) -> dict:
    description = page.get("description", "")
    suggestions = JDParser.analyze(description, page.get("title") or None)
    return {
        **page,
        "required_skills": suggestions["required_skills"],
        "preferred_skills": suggestions["preferred_skills"],
        "experience_years": suggestions["experience_years"],
        "education_required": page.get("education_required") or suggestions["education_required"],
        "required_languages": suggestions["languages"],
        "review_required": True,
    }


@router.post("/import-url")
def import_jd_url(payload: JDUrlImportRequest, current_user=Depends(require_recruiter_or_admin)):
    try:
        page = fetch_job_page(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if page.get("postings") is not None:
        page["postings"] = [_add_jd_suggestions(posting) for posting in page["postings"] if len(posting.get("description", "").strip()) >= 30][:40]
        if not page["postings"]:
            raise HTTPException(status_code=422, detail="Không tìm thấy tin có mô tả đủ nội dung trên bảng tin này.")
        return page
    return _add_jd_suggestions(page)


@router.post("/parse-text")
def parse_jd_text(payload: JDTextImportRequest, current_user=Depends(require_recruiter_or_admin)):
    text_content = payload.text.strip()
    if len(text_content) < 30:
        raise HTTPException(status_code=422, detail="Nội dung JD quá ngắn để phân tích. Hãy dán phần mô tả đầy đủ.")
    if looks_like_job_listing(payload.title or "", text_content):
        raise HTTPException(status_code=422, detail="Nội dung có vẻ là trang danh sách/tìm kiếm việc làm. Hãy dán riêng phần mô tả của một tin tuyển dụng.")
    return _add_jd_suggestions({
        "source_url": "",
        "title": (payload.title or "").strip(),
        "company_name": "",
        "department": "",
        "location": "",
        "employment_type": "",
        "experience_required": "",
        "education_required": "",
        "description": text_content,
        "extraction_method": "Văn bản JD do người dùng cung cấp",
    })


@router.post("/parse-file")
def parse_jd_file(file: UploadFile = File(...), current_user=Depends(require_recruiter_or_admin)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file JD PDF, DOCX hoặc TXT.")
    contents = file.file.read(MAX_JD_SIZE_BYTES + 1)
    if len(contents) > MAX_JD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File JD vượt quá giới hạn 5 MB.")
    if suffix == ".txt":
        text_content = contents.decode("utf-8-sig", errors="replace")
    else:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            handle.write(contents)
            temp_path = handle.name
        try:
            text_content = CVParser.read_file(temp_path)
        except pytesseract.TesseractNotFoundError as exc:
            raise HTTPException(status_code=422, detail="Máy chủ chưa cài bộ đọc OCR cho file scan.") from exc
        except pytesseract.TesseractError as exc:
            raise HTTPException(status_code=422, detail="Không đọc được file scan. Hãy kiểm tra OCR tiếng Anh và tiếng Việt trên máy chủ.") from exc
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Không thể đọc file JD này. Hãy thử lưu thành PDF có thể chọn văn bản hoặc DOCX/TXT.") from exc
        finally:
            Path(temp_path).unlink(missing_ok=True)
    if len((text_content or "").strip()) < 30:
        raise HTTPException(status_code=422, detail="Không trích xuất được đủ chữ từ file. Nếu đây là PDF scan, hãy kiểm tra OCR hoặc dán nội dung JD.")
    if looks_like_job_listing("", text_content):
        raise HTTPException(status_code=422, detail="File có vẻ chứa trang danh sách/tìm kiếm việc làm. Hãy tải file JD riêng của một vị trí.")
    return {
        **_add_jd_suggestions({
            "source_url": "",
            "title": "",
            "company_name": "",
            "department": "",
            "location": "",
            "employment_type": "",
            "experience_required": "",
            "education_required": "",
            "description": text_content[:60_000],
            "extraction_method": "Trích xuất từ file JD",
        }),
        "filename": file.filename,
    }


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
    match_ids = [match_id for (match_id,) in db.query(Match.id).filter(Match.job_id == job_id).all()]
    if match_ids:
        from app.models.match_detail import MatchDetail

        db.query(MatchDetail).filter(MatchDetail.match_id.in_(match_ids)).delete(synchronize_session=False)
        db.query(Match).filter(Match.id.in_(match_ids)).delete(synchronize_session=False)
    db.query(AnalysisLog).filter(
        AnalysisLog.entity_type == "job",
        AnalysisLog.entity_id == job_id,
    ).delete(synchronize_session=False)
    from app.api.routes.pipeline import Application, ApplicationEvent
    db.query(ApplicationEvent).filter(ApplicationEvent.job_id == job_id).delete(synchronize_session=False)
    db.query(Application).filter(Application.job_id == job_id).delete(synchronize_session=False)
    db.delete(job)
    db.commit()
    return {"success": True, "message": "Job and its evaluation results deleted"}


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
    return {
        "job_id": job_id,
        "filename": file.filename,
        "description": text_content[:60_000],
        "suggestions": suggestions,
        "applied": False,
    }
