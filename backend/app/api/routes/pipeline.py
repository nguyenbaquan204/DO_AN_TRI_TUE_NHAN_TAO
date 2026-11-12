"""Recruiter-owned workflow, independent of machine ranking."""
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, UniqueConstraint, update
from sqlalchemy.orm import Session
from app.core.database import Base, get_db
from app.core.security import require_recruiter_or_admin
from app.models.job import Job
from app.models.candidate import Candidate

router = APIRouter()
class Application(Base):
    __tablename__ = 'applications'
    __table_args__ = (UniqueConstraint('job_id','candidate_id'),)
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, nullable=False)
    candidate_id = Column(Integer, nullable=False)
    stage = Column(String(30), nullable=False, default='new')
    version = Column(Integer, nullable=False, default=0)

class ApplicationEvent(Base):
    __tablename__ = 'application_events'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, nullable=False)
    candidate_id = Column(Integer, nullable=False)
    previous_stage = Column(String(30), nullable=False)
    stage = Column(String(30), nullable=False)
    note = Column(Text, nullable=False)
    actor = Column(String(255), nullable=False)
    actor_id = Column(Integer, nullable=False)
    created_at = Column(String(50), nullable=False)

class Change(BaseModel):
    stage: Literal['new','review','interview','offer','hired','rejected','withdrawn']
    note: str = Field(min_length=3, max_length=3000)
    version: int = Field(ge=0)

def check(db, job_id, candidate_id=None):
    if not db.get(Job,job_id): raise HTTPException(404,'Không tìm thấy vị trí')
    if candidate_id is not None and not db.get(Candidate,candidate_id): raise HTTPException(404,'Không tìm thấy ứng viên')

@router.get('/{job_id}')
def listing(job_id: int, db: Session=Depends(get_db), user=Depends(require_recruiter_or_admin)):
    check(db,job_id)
    return [{"candidate_id": a.candidate_id,"stage":a.stage,"version":a.version} for a in db.query(Application).filter_by(job_id=job_id).all()]

@router.get('/{job_id}/{candidate_id}')
def history(job_id: int, candidate_id: int, db: Session=Depends(get_db), user=Depends(require_recruiter_or_admin)):
    check(db,job_id,candidate_id)
    a=db.query(Application).filter_by(job_id=job_id,candidate_id=candidate_id).first()
    events=db.query(ApplicationEvent).filter_by(job_id=job_id,candidate_id=candidate_id).order_by(ApplicationEvent.id.desc()).all()
    return {"stage":a.stage if a else 'new',"version":a.version if a else 0,
            "events":[{"id":e.id,"previous_stage":e.previous_stage,"stage":e.stage,"note":e.note,"actor":e.actor,"created_at":e.created_at} for e in events]}

@router.put('/{job_id}/{candidate_id}')
def change(job_id: int,candidate_id: int,payload: Change,db: Session=Depends(get_db),user=Depends(require_recruiter_or_admin)):
    check(db,job_id,candidate_id)
    if len(payload.note.strip())<3: raise HTTPException(422,'Hãy ghi lý do hoặc nhận xét ít nhất 3 ký tự')
    from sqlalchemy.exc import IntegrityError
    try:
        a=db.query(Application).filter_by(job_id=job_id,candidate_id=candidate_id).first()
        if a is None:
            a=Application(job_id=job_id,candidate_id=candidate_id,stage='new',version=0)
            db.add(a);db.flush()
        previous=a.stage
        result=db.execute(update(Application).where(Application.id==a.id,Application.version==payload.version).values(stage=payload.stage,version=payload.version+1))
        if result.rowcount!=1:
            db.rollback();raise HTTPException(409,'Dữ liệu vừa được thay đổi. Đóng và mở lại hồ sơ trước khi lưu.')
        db.add(ApplicationEvent(job_id=job_id,candidate_id=candidate_id,previous_stage=previous,
            stage=payload.stage,note=payload.note.strip(),actor=user.name,actor_id=user.id,
            created_at=datetime.now(timezone.utc).isoformat()))
        db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Dữ liệu vừa được thay đổi. Hãy mở lại hồ sơ.')
    return history(job_id,candidate_id,db,user)
