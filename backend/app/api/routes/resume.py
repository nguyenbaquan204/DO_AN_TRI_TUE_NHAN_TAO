import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
import pytesseract
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import require_recruiter_or_admin
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.services.cv_information_extractor import CVInformationExtractor
from app.services.cv_parser import CVParser
from app.services.skill_extractor import SkillExtractor

router = APIRouter()
settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


def _process_upload(file: UploadFile, db: Session):
    if file.filename is None or not file.filename.strip():
        raise HTTPException(status_code=400, detail="Filename is required")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF or DOCX")
    uploads_dir = Path(settings.upload_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    saved_path = uploads_dir / f"{uuid.uuid4().hex}{ext}"
    contents = file.file.read(MAX_FILE_SIZE_BYTES + 1)
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 5MB limit")
    saved_path.write_bytes(contents)
    try:
        extracted_text = CVParser.read_file(str(saved_path))
    except pytesseract.TesseractNotFoundError as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Chưa cài Tesseract OCR trên máy chủ để đọc CV scan.") from exc
    except pytesseract.TesseractError as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="OCR không đọc được trang scan. Hãy kiểm tra dữ liệu ngôn ngữ Anh và Việt của Tesseract.") from exc
    except Exception as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Unable to extract text from CV") from exc
    if not extracted_text.strip():
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Không tìm thấy nội dung có thể đọc trong CV.")
    skills = SkillExtractor.extract(extracted_text)
    extracted_name = CVInformationExtractor.extract_name(extracted_text) or file.filename
    links = CVInformationExtractor.extract_links(extracted_text)
    candidate = Candidate(
        full_name=extracted_name,
        email=CVInformationExtractor.extract_email(extracted_text),
        phone=CVInformationExtractor.extract_phone(extracted_text),
        location=CVInformationExtractor.extract_location(extracted_text),
        linkedin=links.get("linkedin"), github=links.get("github"), portfolio=links.get("portfolio"),
        raw_text=extracted_text, summary=extracted_text[:500], skills=skills,
        experience_years=CVInformationExtractor.extract_experience_years(extracted_text),
        education=CVInformationExtractor.extract_education(extracted_text),
        work_experience=CVInformationExtractor.extract_work_experience(extracted_text),
        projects=CVInformationExtractor.extract_projects(extracted_text),
        certificates=CVInformationExtractor.extract_certificates(extracted_text),
        languages=CVInformationExtractor.extract_languages(extracted_text),
        analysis_status="COMPLETED",
    )
    db.add(candidate)
    db.flush()
    resume_record = Resume(candidate_id=candidate.id, file_name=file.filename, file_path=str(saved_path),
                           extracted_text=extracted_text, analysis_status="COMPLETED", analysis_version="v1")
    db.add(resume_record)
    db.commit()
    db.refresh(candidate)
    db.refresh(resume_record)
    return {"success": True, "candidate_id": candidate.id, "resume_id": resume_record.id,
            "file_name": file.filename, "candidate_name": candidate.full_name,
            "analysis_status": "COMPLETED",
            "extracted_text_preview": extracted_text[:500]}


@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_recruiter_or_admin),
):
    return _process_upload(file, db)


@router.post("/upload-batch")
def upload_batch(files: list[UploadFile] = File(...), job_id: int | None = Form(None), db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    results = []
    for file in files:
        try:
            results.append(_process_upload(file, db))
        except HTTPException as exc:
            results.append({"success": False, "file_name": file.filename, "analysis_status": "FAILED", "error": exc.detail})
    return {"job_id": job_id, "results": results, "completed": sum(item.get("success", False) for item in results), "failed": sum(not item.get("success", False) for item in results)}
