from typing import List

from pydantic import BaseModel, Field


class MatchingRequest(BaseModel):
    cv_text: str = Field(..., min_length=1, max_length=100_000)
    jd_text: str = Field(..., min_length=1, max_length=100_000)
    candidate_skills: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)


class BatchScreenRequest(BaseModel):
    candidate_ids: List[int] = Field(..., min_length=1, max_length=100)


class MatchingResponse(BaseModel):
    overall_score: float
    skill_score: float
    experience_score: float
    education_score: float
    project_score: float
    semantic_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    experience_gap: float
    explanation: List[str]
