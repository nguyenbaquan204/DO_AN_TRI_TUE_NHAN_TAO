from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlsplit


class JobBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    company_name: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    description: str = Field(..., min_length=10)
    source_url: Optional[str] = Field(None, max_length=2048)
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

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value):
        if value is None or not value.strip():
            return None
        parts = urlsplit(value.strip())
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
            raise ValueError("Nguồn công việc phải là đường dẫn HTTP hoặc HTTPS hợp lệ.")
        return value.strip()


class JobCreate(JobBase):
    pass


class JobUpdate(JobBase):
    pass


class JobOut(JobBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
