from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class JobBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    department: Optional[str] = None
    location: Optional[str] = None
    description: str = Field(..., min_length=10)
    employment_type: Optional[str] = None
    experience_required: Optional[str] = None
    education_required: Optional[str] = None
    salary: Optional[str] = None
    status: Literal["open", "closed"] = "open"
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    education_level: Optional[str] = None
    majors: List[str] = Field(default_factory=list)
    maximum_experience_years: Optional[float] = Field(None, ge=0)
    relevant_experience_required: bool = False
    required_certificates: List[str] = Field(default_factory=list)
    preferred_certificates: List[str] = Field(default_factory=list)
    required_languages: List[str] = Field(default_factory=list)
    preferred_languages: List[str] = Field(default_factory=list)


class JobCreate(JobBase):
    pass


class JobUpdate(JobBase):
    pass


class JobOut(JobBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
