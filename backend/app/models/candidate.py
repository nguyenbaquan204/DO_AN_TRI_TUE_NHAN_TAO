from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    linkedin = Column(String(255), nullable=True)
    github = Column(String(255), nullable=True)
    portfolio = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    experience_years = Column(Float, default=0.0, nullable=False)
    skills = Column(JSON, nullable=True)
    education = Column(JSON, nullable=True)
    work_experience = Column(JSON, nullable=True)
    projects = Column(JSON, nullable=True)
    certificates = Column(JSON, nullable=True)
    languages = Column(JSON, nullable=True)
    analysis_status = Column(String(30), default="COMPLETED", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    resumes = relationship("Resume", back_populates="candidate")
    matches = relationship("Match", back_populates="candidate")
