from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.ai.matching_engine import MatchingEngine
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import require_recruiter_or_admin
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match import Match
from app.models.match_detail import MatchDetail
from app.schemas.matching import BatchScreenRequest, MatchingRequest
from app.services.jd_parser import JDParser
from app.services.skill_extractor import SkillExtractor
from training.predict import SuitabilityPredictor

router = APIRouter()
engine = MatchingEngine(get_settings().model_name)
predictor = SuitabilityPredictor()
predictor.builder.matching_engine = engine
# The checked-in classifier was trained with this feature disabled and expects
# zero at inference unless it is explicitly retrained with real embeddings.
predictor.builder.semantic_enabled = False


def _resolve_job_requirements(job, analysis: dict) -> dict:
    structured_experience = JDParser.extract_experience_years(job.experience_required or "")
    return {
        # An explicitly empty list means the recruiter cleared that criterion.
        # Fall back to JD parsing only for legacy rows where the value is NULL.
        "required_skills": job.required_skills if job.required_skills is not None else analysis.get("required_skills", []),
        "preferred_skills": job.preferred_skills if job.preferred_skills is not None else analysis.get("preferred_skills", []),
        "required_experience_years": structured_experience or analysis.get("experience_years", 0.0),
        "education_required": job.education_required or job.education_level or analysis.get("education_required"),
    }


@router.post("/jobs/{job_id}/match/{candidate_id}")
def create_match(job_id: int, candidate_id: int, db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    text_parts = [candidate.raw_text or ""]
    if candidate.experience_years:
        text_parts.append(f"{candidate.experience_years:g} years experience")
    education = candidate.education or {}
    if isinstance(education, dict) and education.get("text"):
        text_parts.append(str(education["text"]))
    elif isinstance(education, str) and education.strip():
        text_parts.append(education)
    cv_text = "\n".join(part for part in text_parts if part)
    jd_analysis = JDParser.analyze(job.description, job.title)
    requirements = _resolve_job_requirements(job, jd_analysis)
    required_skills = requirements["required_skills"]
    preferred_skills = requirements["preferred_skills"]
    candidate_skills = SkillExtractor.normalize_skills((candidate.skills or []) + SkillExtractor.extract(cv_text))
    score = engine.score_candidate(cv_text, job.description, candidate_skills, required_skills, requirements["required_experience_years"], requirements["education_required"])
    prediction = predictor.predict(
        cv_text,
        job.description,
        required_skills,
        preferred_skills,
        requirements["required_experience_years"],
        requirements["education_required"],
    ) if predictor.available else None
    feature_snapshot = (prediction["feature_snapshot"] if prediction else {})
    feature_snapshot.update({
        "major_match": None,
        "certificate_match_ratio": None,
        "language_match_ratio": None,
        "semantic_model_available": engine.embedding_status == "sentence-transformer",
    })

    match_record = db.query(Match).filter(
        Match.job_id == job_id,
        Match.candidate_id == candidate_id,
    ).first()
    if match_record is None:
        match_record = Match(job_id=job_id, candidate_id=candidate_id)
    else:
        db.query(MatchDetail).filter(MatchDetail.match_id == match_record.id).delete(synchronize_session=False)
    match_record.overall_score = score["overall_score"]
    match_record.skill_score = score["skill_score"]
    match_record.experience_score = score["experience_score"]
    match_record.education_score = score["education_score"]
    match_record.project_score = score["project_score"]
    match_record.semantic_score = score["semantic_score"]
    match_record.predicted_class = prediction["predicted_class"] if prediction else None
    match_record.model_confidence = prediction["model_confidence"] if prediction else None
    match_record.model_version = prediction["model_version"] if prediction else None
    match_record.prediction_mode = "trained-model" if prediction else "fallback"
    match_record.feature_snapshot = feature_snapshot
    db.add(match_record)
    db.flush()

    for skill in score["matched_skills"]:
        db.add(MatchDetail(match_id=match_record.id, skill_name=skill, match_type="REQUIRED", score=100, status="MATCHED", description=f"Skill matched with job requirement: {skill}"))
    for skill in score["missing_skills"]:
        db.add(MatchDetail(match_id=match_record.id, skill_name=skill, match_type="REQUIRED", score=0, status="MISSING", description=f"Skill missing from candidate profile: {skill}"))
    for skill in score["additional_skills"]:
        db.add(MatchDetail(match_id=match_record.id, skill_name=skill, match_type="OPTIONAL", score=40, status="ADDITIONAL", description=f"Candidate has skill not explicitly required: {skill}"))
    db.commit()
    db.refresh(match_record)

    return {
        "id": match_record.id,
        "job_id": job_id,
        "candidate_id": candidate_id,
        **score,
        "prediction_mode": "trained-model" if prediction else "fallback",
        **(prediction or {}),
        "feature_snapshot": feature_snapshot,
    }


@router.get("/jobs/{job_id}/matches")
def list_job_matches(job_id: int, suitability: str | None = None, min_confidence: float | None = Query(None, ge=0.0, le=1.0), search: str | None = None, db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    matches = db.query(Match).filter(Match.job_id == job_id).order_by(Match.updated_at.desc(), Match.id.desc()).all()
    latest_by_candidate = {}
    for item in matches:
        latest_by_candidate.setdefault(item.candidate_id, item)
    matches = list(latest_by_candidate.values())
    if suitability:
        matches = [item for item in matches if item.predicted_class == suitability.upper()]
    if min_confidence is not None:
        matches = [item for item in matches if (item.model_confidence or 0) >= min_confidence]
    # Rank by the transparent evidence score. Classifier labels are secondary
    # signals because the current research model is not a strong benchmark.
    matches = sorted(matches, key=lambda item: (-item.overall_score, {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(item.predicted_class, 3), -(item.model_confidence or 0)))
    output = []
    for item in matches:
        candidate = db.query(Candidate).filter(Candidate.id == item.candidate_id).first()
        if candidate is None:
            continue
        if search and search.lower() not in (candidate.full_name or "").lower() and search.lower() not in (candidate.email or "").lower():
            continue
        output.append({
            "id": item.id,
            "candidate_id": item.candidate_id,
            "candidate_name": candidate.full_name if candidate else "Unknown",
            "overall_score": item.overall_score,
            "skill_score": item.skill_score,
            "semantic_score": item.semantic_score,
            "predicted_class": item.predicted_class,
            "model_confidence": item.model_confidence,
            "prediction_mode": item.prediction_mode or ("trained-model" if item.model_version else "fallback"),
        })
    return output


@router.post("/jobs/{job_id}/screen-batch")
def screen_batch(job_id: int, payload: BatchScreenRequest, db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    candidate_ids = payload.candidate_ids
    results = []
    for candidate_id in candidate_ids:
        try:
            result = create_match(job_id, int(candidate_id), db, current_user)
            results.append({"success": True, "candidate_id": candidate_id, "result": result})
        except HTTPException as exc:
            results.append({"success": False, "candidate_id": candidate_id, "error": exc.detail})
    return {"results": results, "completed": sum(item["success"] for item in results), "failed": sum(not item["success"] for item in results)}


@router.get("/matches/{match_id}")
def get_match_detail(match_id: int, db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    details = db.query(MatchDetail).filter(MatchDetail.match_id == match_id).all()
    return {
        "id": match.id,
        "job_id": match.job_id,
        "candidate_id": match.candidate_id,
        "overall_score": match.overall_score,
        "skill_score": match.skill_score,
        "experience_score": match.experience_score,
        "education_score": match.education_score,
        "project_score": match.project_score,
        "semantic_score": match.semantic_score,
        "predicted_class": match.predicted_class,
        "model_confidence": match.model_confidence,
        "model_version": match.model_version,
        "prediction_mode": match.prediction_mode or ("trained-model" if match.model_version else "fallback"),
        "feature_snapshot": match.feature_snapshot,
        "details": [
            {"skill_name": d.skill_name, "match_type": d.match_type, "status": d.status, "score": d.score, "description": d.description} for d in details
        ],
    }


@router.post("/evaluate")
def evaluate_matching(payload: MatchingRequest, db: Session = Depends(get_db), current_user=Depends(require_recruiter_or_admin)):
    score = engine.score_candidate(payload.cv_text, payload.jd_text, payload.candidate_skills, payload.required_skills)
    return score


@router.get("/model/status")
def model_status(current_user=Depends(require_recruiter_or_admin)):
    return {
        "model_available": predictor.available,
        "model_type": "RandomForestClassifier" if predictor.available else None,
        "model_name": "Candidate-Job Suitability Classifier",
        "classes": predictor.metadata.get("classes", ["HIGH", "MEDIUM", "LOW"]) if predictor.available else [],
        "feature_count": len(predictor.metadata.get("feature_names", [])) if predictor.available else 0,
        "model_version": predictor.metadata.get("model_version") if predictor.available else None,
        "prediction_mode": "trained-model" if predictor.available else "fallback",
    }
