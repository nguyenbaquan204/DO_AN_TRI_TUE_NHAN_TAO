from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.services.cv_parser import CVParser
from app.services.cv_information_extractor import CVInformationExtractor
from app.services.demo_data import load_demo_jobs

BASE_DIR = Path(__file__).resolve().parent.parent
CV_DIR = BASE_DIR / "data" / "sample_cvs"
def ensure_tables():
    Base.metadata.create_all(bind=engine)


def load_candidates():
    candidates = []
    for path in sorted(CV_DIR.iterdir()):
        if path.suffix.lower() not in {".pdf", ".docx"}:
            continue
        text = CVParser.read_file(str(path))
        extracted_name = CVInformationExtractor.extract_name(text) or path.stem.replace("_", " ").title()
        email = CVInformationExtractor.extract_email(text)
        phone = CVInformationExtractor.extract_phone(text)
        candidates.append({
            "full_name": extracted_name,
            "email": email,
            "phone": phone,
            "location": "Remote",
            "summary": text[:500],
            "raw_text": text,
        })
    return candidates


def seed_demo_data():
    db = SessionLocal()
    try:
        ensure_tables()
        settings = get_settings()
        admin_email = settings.demo_admin_email.strip().lower()
        if not db.query(User).filter(User.email == admin_email).first():
            db.add(User(
                name="Admin Demo",
                email=admin_email,
                password_hash=get_password_hash(settings.demo_admin_password),
                role="admin",
            ))
        if not db.query(User).filter(User.email == "recruiter@example.com").first():
            db.add(User(
                name="Recruiter Demo",
                email="recruiter@example.com",
                password_hash=get_password_hash("password123"),
                role="recruiter",
            ))
        if db.query(Job).count() == 0:
            db.add_all(Job(**item, status="open", user_id=1) for item in load_demo_jobs())
        if db.query(Candidate).count() == 0:
            for item in load_candidates():
                db.add(Candidate(**item))
        db.commit()
        print(f"Seeded demo data: {db.query(User).count()} users, {db.query(Job).count()} jobs, {db.query(Candidate).count()} candidates")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
