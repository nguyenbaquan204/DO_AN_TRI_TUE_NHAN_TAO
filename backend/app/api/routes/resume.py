import json
import tempfile
import uuid
from pathlib import Path

import pytesseract
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field, ValidationError
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
REVIEW_TEXT_PREVIEW_LENGTH = 12_000


class CandidateReviewPayload(BaseModel):
    """Human-reviewed profile values submitted with the original CV file."""

    full_name: str = Field(..., min_length=1, max_length=255)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    linkedin: str | None = Field(None, max_length=500)
    github: str | None = Field(None, max_length=500)
    portfolio: str | None = Field(None, max_length=500)
    experience_years: float = Field(0, ge=0, le=80)
    skills: list[str] = Field(default_factory=list, max_length=100)
    education: str = Field("", max_length=10_000)
    work_experience: str = Field("", max_length=30_000)
    projects: list[str] = Field(default_factory=list, max_length=100)
    certificates: list[str] = Field(default_factory=list, max_length=100)
    languages: list[str] = Field(default_factory=list, max_length=50)

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        value = value.strip() if value else ""
        return value or None

    def normalized(self) -> dict:
        values = self.model_dump()
        for field in ("email", "phone", "location", "linkedin", "github", "portfolio"):
            values[field] = self._clean_optional(values[field])
        values["full_name"] = values["full_name"].strip()
        values["skills"] = SkillExtractor.normalize_skills(values["skills"])
        for field in ("projects", "certificates", "languages"):
            values[field] = list(dict.fromkeys(item.strip() for item in values[field] if item and item.strip()))
        values["education"] = values["education"].strip()
        values["work_experience"] = values["work_experience"].strip()
        return values


def _read_cv(file: UploadFile) -> tuple[bytes, str, str]:
    if file.filename is None or not file.filename.strip():
        raise HTTPException(status_code=400, detail="Filename is required")
    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF or DOCX")

    contents = file.file.read(MAX_FILE_SIZE_BYTES + 1)
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 5MB limit")

    uploads_dir = Path(settings.upload_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=extension, prefix="cv-preview-", dir=uploads_dir, delete=False) as handle:
        temp_path = Path(handle.name)
        handle.write(contents)
    try:
        extracted_text = CVParser.read_file(str(temp_path))
    except pytesseract.TesseractNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Chưa cài Tesseract OCR trên máy chủ để đọc CV scan.") from exc
    except pytesseract.TesseractError as exc:
        raise HTTPException(status_code=422, detail="OCR không đọc được trang scan. Hãy kiểm tra dữ liệu ngôn ngữ Anh và Việt của Tesseract.") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Không thể trích xuất văn bản từ CV. Hãy thử một file PDF có thể chọn chữ hoặc DOCX.") from exc
    finally:
        temp_path.unlink(missing_ok=True)

    if not extracted_text.strip():
        raise HTTPException(status_code=422, detail="Không tìm thấy nội dung có thể đọc trong CV.")
    return contents, extension, extracted_text


def _extract_candidate_data(text: str, filename: str) -> dict:
    links = CVInformationExtractor.extract_links(text)
    education = CVInformationExtractor.extract_education(text) or {}
    experience = CVInformationExtractor.extract_work_experience(text) or {}
    return {
        "full_name": CVInformationExtractor.extract_name(text) or Path(filename).stem[:255] or "Ứng viên chưa rõ tên",
        "email": CVInformationExtractor.extract_email(text),
        "phone": CVInformationExtractor.extract_phone(text),
        "location": CVInformationExtractor.extract_location(text),
        "linkedin": links.get("linkedin"),
        "github": links.get("github"),
        "portfolio": links.get("portfolio"),
        "experience_years": CVInformationExtractor.extract_experience_years(text),
        "skills": SkillExtractor.extract(text),
        "education": str(education.get("text", "")) if isinstance(education, dict) else str(education or ""),
        "work_experience": str(experience.get("text", "")) if isinstance(experience, dict) else str(experience or ""),
        "projects": CVInformationExtractor.extract_projects(text),
        "certificates": CVInformationExtractor.extract_certificates(text),
        "languages": CVInformationExtractor.extract_languages(text),
    }


def _preview_result(file: UploadFile) -> dict:
    _, _, extracted_text = _read_cv(file)
    candidate_data = _extract_candidate_data(extracted_text, file.filename or "CV")
    return {
        "success": True,
        "file_name": file.filename,
        "candidate_name": candidate_data["full_name"],
        "candidate_data": candidate_data,
        "analysis_status": "REVIEW_REQUIRED",
        "extraction_method": "Trích xuất văn bản và luật nhận diện hồ sơ; cần người dùng kiểm tra.",
        "extracted_text_preview": extracted_text[:REVIEW_TEXT_PREVIEW_LENGTH],
        "extracted_text_truncated": len(extracted_text) > REVIEW_TEXT_PREVIEW_LENGTH,
    }


@router.post("/preview")
def preview_resume(file: UploadFile = File(...), current_user=Depends(require_recruiter_or_admin)):
    """Extract profile suggestions without creating a candidate or storing the file."""
    return _preview_result(file)


def _process_upload(file: UploadFile, candidate_data: str, db: Session):
    if not candidate_data:
        raise HTTPException(status_code=422, detail="Hãy phân tích và kiểm tra thông tin CV trước khi lưu hồ sơ.")
    try:
        review = CandidateReviewPayload.model_validate(json.loads(candidate_data)).normalized()
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise HTTPException(status_code=422, detail="Thông tin đã xác nhận không đúng định dạng. Hãy kiểm tra các trường rồi thử lại.") from exc

    contents, extension, extracted_text = _read_cv(file)
    uploads_dir = Path(settings.upload_dir)
    saved_path = uploads_dir / f"{uuid.uuid4().hex}{extension}"
    saved_path.write_bytes(contents)
    try:
        candidate = Candidate(
            full_name=review["full_name"],
            email=review["email"],
            phone=review["phone"],
            location=review["location"],
            linkedin=review["linkedin"],
            github=review["github"],
            portfolio=review["portfolio"],
            raw_text=extracted_text,
            summary=extracted_text[:500],
            skills=review["skills"],
            experience_years=review["experience_years"],
            education={"text": review["education"]} if review["education"] else {},
            work_experience={"text": review["work_experience"]} if review["work_experience"] else {},
            projects=review["projects"],
            certificates=review["certificates"],
            languages=review["languages"],
            analysis_status="COMPLETED",
        )
        db.add(candidate)
        db.flush()
        resume_record = Resume(
            candidate_id=candidate.id,
            file_name=file.filename or saved_path.name,
            file_path=str(saved_path),
            extracted_text=extracted_text,
            analysis_status="COMPLETED",
            analysis_version="reviewed-v2",
        )
        db.add(resume_record)
        db.commit()
        db.refresh(candidate)
        db.refresh(resume_record)
    except Exception:
        db.rollback()
        saved_path.unlink(missing_ok=True)
        raise

    return {
        "success": True,
        "candidate_id": candidate.id,
        "resume_id": resume_record.id,
        "file_name": file.filename,
        "candidate_name": candidate.full_name,
        "analysis_status": "COMPLETED",
    }


@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    candidate_data: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_recruiter_or_admin),
):
    return _process_upload(file, candidate_data, db)


@router.post("/upload-batch")
def upload_batch(
    files: list[UploadFile] = File(...),
    job_id: int | None = Form(None),
    current_user=Depends(require_recruiter_or_admin),
):
    """Batch extraction preview. Saving each candidate requires the reviewed /upload step."""
    results = []
    for file in files:
        try:
            results.append(_preview_result(file))
        except HTTPException as exc:
            results.append({"success": False, "file_name": file.filename, "analysis_status": "FAILED", "error": exc.detail})
    return {
        "job_id": job_id,
        "results": results,
        "completed": sum(item.get("success", False) for item in results),
        "failed": sum(not item.get("success", False) for item in results),
    }
