"""One input contract for online ranking and offline evaluation."""
from app.services.jd_parser import JDParser
from app.services.skill_extractor import SkillExtractor

SCORING_VERSION = "reviewed-profile-v2"


def section_text(value):
    if isinstance(value, dict):
        return str(value.get("text", "") or "").strip()
    if isinstance(value, list):
        return "\n".join(section_text(item) for item in value if item)
    return str(value or "").strip()


def resolve_requirements(job, analysis=None):
    analysis = analysis if analysis is not None else JDParser.analyze(job.description, job.title)
    return {
        "required_skills": job.required_skills if job.required_skills is not None else analysis.get("required_skills", []),
        "preferred_skills": job.preferred_skills if job.preferred_skills is not None else analysis.get("preferred_skills", []),
        "required_experience_years": JDParser.extract_experience_years(job.experience_required) if job.experience_required is not None else analysis.get("experience_years", 0.0),
        "education_required": job.education_required if job.education_required is not None else (job.education_level if job.education_level is not None else analysis.get("education_required")),
    }


def candidate_inputs(candidate):
    raw = candidate.raw_text or ""
    fields = ("skills", "education", "work_experience", "projects", "certificates", "languages")
    structured = any(getattr(candidate, field, None) is not None for field in fields)
    parts = [section_text(getattr(candidate, field, None)) for field in fields]
    years = candidate.experience_years
    if structured and years:
        parts.append(f"{years:g} years experience")
    text = "\n".join(part for part in parts if part) if structured else raw
    return {
        "cv_text": text,
        "candidate_skills": SkillExtractor.normalize_skills(candidate.skills if candidate.skills is not None else SkillExtractor.extract(raw)),
        "candidate_experience_years": years if structured else None,
        "candidate_education": section_text(candidate.education) if candidate.education is not None else None,
        "candidate_projects": candidate.projects,
    }


def scoring_inputs(candidate, job):
    requirements = resolve_requirements(job)
    return {**candidate_inputs(candidate), "jd_text": job.description or "",
            "required_skills": requirements["required_skills"],
            "required_experience_years": requirements["required_experience_years"],
            "education_required": requirements["education_required"]}
