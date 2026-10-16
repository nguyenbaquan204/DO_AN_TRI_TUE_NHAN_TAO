from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    employment_type = Column(String(100), nullable=True)
    experience_required = Column(String(50), nullable=True)
    education_required = Column(String(255), nullable=True)
    salary = Column(String(100), nullable=True)
    status = Column(String(50), default="open", nullable=False)
    created_by = Column(Integer, nullable=False, default=1)
    analysis_summary = Column(Text, nullable=True)
    required_skills = Column(JSON, nullable=True)
    preferred_skills = Column(JSON, nullable=True)
    education_level = Column(String(100), nullable=True)
    majors = Column(JSON, nullable=True)
    maximum_experience_years = Column(Float, nullable=True)
    relevant_experience_required = Column(Integer, default=0, nullable=False)
    required_certificates = Column(JSON, nullable=True)
    preferred_certificates = Column(JSON, nullable=True)
    required_languages = Column(JSON, nullable=True)
    preferred_languages = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    user_id = Column(Integer, nullable=False, default=1)

    matches = relationship("Match", back_populates="job")
