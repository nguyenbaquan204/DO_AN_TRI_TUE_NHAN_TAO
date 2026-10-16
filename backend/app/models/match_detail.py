from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MatchDetail(Base):
    __tablename__ = "match_details"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    skill_name = Column(String(255), nullable=False)
    match_type = Column(String(50), nullable=False)
    score = Column(Integer, default=0, nullable=False)
    status = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    match = relationship("Match", back_populates="details")
