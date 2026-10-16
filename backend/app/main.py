from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.api.routes.auth import router as auth_router
from app.api.routes.candidates import router as candidates_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.matching import router as matching_router
from app.api.routes.model import router as model_router
from app.api.routes.resume import router as resume_router
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.analysis_log import AnalysisLog
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match import Match
from app.models.match_detail import MatchDetail
from app.models.resume import Resume
from app.models.user import User
from app.services.demo_data import load_demo_jobs

settings = get_settings()


def ensure_schema_compatibility():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if not inspector.has_table("jobs"):
        Base.metadata.create_all(bind=engine)
        return

    with engine.begin() as connection:
        table_columns = {
            "jobs": {column["name"] for column in inspector.get_columns("jobs")},
            "candidates": {column["name"] for column in inspector.get_columns("candidates")},
            "matches": {column["name"] for column in inspector.get_columns("matches")} if inspector.has_table("matches") else set(),
        }

        if "created_by" not in table_columns["jobs"]:
            connection.execute(text("ALTER TABLE jobs ADD COLUMN created_by INTEGER NOT NULL DEFAULT 1"))
        if "analysis_summary" not in table_columns["jobs"]:
            connection.execute(text("ALTER TABLE jobs ADD COLUMN analysis_summary TEXT"))
        if "required_skills" not in table_columns["jobs"]:
            connection.execute(text("ALTER TABLE jobs ADD COLUMN required_skills JSON"))
        if "preferred_skills" not in table_columns["jobs"]:
            connection.execute(text("ALTER TABLE jobs ADD COLUMN preferred_skills JSON"))
        for column, definition in {
            "education_level": "VARCHAR(100)",
            "majors": "JSON",
            "maximum_experience_years": "FLOAT",
            "relevant_experience_required": "INTEGER NOT NULL DEFAULT 0",
            "required_certificates": "JSON",
            "preferred_certificates": "JSON",
            "required_languages": "JSON",
            "preferred_languages": "JSON",
        }.items():
            if column not in table_columns["jobs"]:
                connection.execute(text(f"ALTER TABLE jobs ADD COLUMN {column} {definition}"))
        for column in (
            "required_skills",
            "preferred_skills",
            "majors",
            "required_certificates",
            "preferred_certificates",
            "required_languages",
            "preferred_languages",
        ):
            connection.execute(text(f"UPDATE jobs SET {column} = '[]' WHERE {column} IS NULL"))
        connection.execute(text("UPDATE jobs SET relevant_experience_required = 0 WHERE relevant_experience_required IS NULL"))
        candidate_columns = table_columns["candidates"]
        for column, definition in {
            "skills": "JSON",
            "education": "JSON",
            "work_experience": "JSON",
            "projects": "JSON",
            "certificates": "JSON",
            "languages": "JSON",
            "analysis_status": "VARCHAR(30) NOT NULL DEFAULT 'COMPLETED'",
        }.items():
            if column not in candidate_columns:
                connection.execute(text(f"ALTER TABLE candidates ADD COLUMN {column} {definition}"))
        if "summary" not in table_columns["candidates"]:
            connection.execute(text("ALTER TABLE candidates ADD COLUMN summary TEXT"))
        if "experience_years" not in table_columns["candidates"]:
            connection.execute(text("ALTER TABLE candidates ADD COLUMN experience_years FLOAT NOT NULL DEFAULT 0.0"))
        if "predicted_class" not in table_columns["matches"]:
            connection.execute(text("ALTER TABLE matches ADD COLUMN predicted_class VARCHAR(20)"))
        if "model_confidence" not in table_columns["matches"]:
            connection.execute(text("ALTER TABLE matches ADD COLUMN model_confidence FLOAT"))
        if "model_version" not in table_columns["matches"]:
            connection.execute(text("ALTER TABLE matches ADD COLUMN model_version VARCHAR(100)"))
        if "prediction_mode" not in table_columns["matches"]:
            connection.execute(text("ALTER TABLE matches ADD COLUMN prediction_mode VARCHAR(30)"))
        if "feature_snapshot" not in table_columns["matches"]:
            connection.execute(text("ALTER TABLE matches ADD COLUMN feature_snapshot JSON"))


def seed_demo_data():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == settings.demo_admin_email.strip().lower()).first():
            db.add(User(
                name="Admin Demo",
                email=settings.demo_admin_email.strip().lower(),
                password_hash=get_password_hash(settings.demo_admin_password),
                role="admin",
            ))
        if not db.query(User).filter(User.email == "recruiter@example.com").first():
            recruiter = User(
                name="Recruiter Demo",
                email="recruiter@example.com",
                password_hash=get_password_hash("password123"),
                role="recruiter",
            )
            db.add(recruiter)
            db.commit()
            db.refresh(recruiter)
        if not db.query(Job).count():
            db.add_all(Job(**item, status="open", user_id=1) for item in load_demo_jobs())
        if not db.query(Candidate).count():
            db.add_all(
                [
                    Candidate(full_name="Nguyen Van A", email="a@example.com", phone="0900000001", location="HCMC", raw_text="Java Spring Boot MySQL Docker REST APIs backend engineer."),
                    Candidate(full_name="Tran Thi B", email="b@example.com", phone="0900000002", location="Hanoi", raw_text="React TypeScript Node.js SQL frontend developer."),
                ]
            )
        db.commit()
    finally:
        db.close()


app = FastAPI(title="AI Recruitment Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_schema_compatibility()
Base.metadata.create_all(bind=engine)
if settings.seed_demo_data:
    seed_demo_data()

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(candidates_router, prefix="/api/candidates", tags=["Candidates"])
app.include_router(resume_router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(matching_router, prefix="/api/matching", tags=["Matching"])
app.include_router(model_router, prefix="/api/model", tags=["Model"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "AI Recruitment Assistant API"}
