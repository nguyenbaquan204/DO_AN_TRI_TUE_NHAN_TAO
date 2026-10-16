from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    overall_score = Column(Float, default=0.0, nullable=False)
    skill_score = Column(Float, default=0.0, nullable=False)
    experience_score = Column(Float, default=0.0, nullable=False)
    education_score = Column(Float, default=0.0, nullable=False)
    project_score = Column(Float, default=0.0, nullable=False)
    semantic_score = Column(Float, default=0.0, nullable=False)
    predicted_class = Column(String(20), nullable=True)
    model_confidence = Column(Float, nullable=True)
    model_version = Column(String(100), nullable=True)
    prediction_mode = Column(String(30), nullable=True)
    feature_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    job = relationship("Job", back_populates="matches")
    candidate = relationship("Candidate", back_populates="matches")
    details = relationship("MatchDetail", back_populates="match")
