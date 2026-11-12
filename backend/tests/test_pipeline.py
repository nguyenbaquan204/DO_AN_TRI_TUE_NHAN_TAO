import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.database import Base
from app.models.resume import Resume
from app.models.match import Match
from app.models.match_detail import MatchDetail
from app.api.routes.pipeline import Job,Candidate,Change,change,history,listing

class PipelineTest(unittest.TestCase):
 def test_separate_jobs_history_and_conflict(self):
  engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(engine)
  with Session(engine) as db:
   j1=Job(title='A',description='Python');j2=Job(title='B',description='Python');c=Candidate(full_name='Test')
   db.add_all([j1,j2,c]);db.commit();user=SimpleNamespace(id=1,name='Reviewer')
   result=change(j1.id,c.id,Change(stage='interview',note='Schedule technical interview',version=0),db,user)
   self.assertEqual(result['stage'],'interview');self.assertEqual(len(result['events']),1)
   self.assertEqual(history(j2.id,c.id,db,user)['stage'],'new')
   with self.assertRaises(HTTPException) as error: change(j1.id,c.id,Change(stage='hired',note='stale update',version=0),db,user)
   self.assertEqual(error.exception.status_code,409)
   result=change(j1.id,c.id,Change(stage='interview',note='Additional note',version=1),db,user)
   self.assertEqual(len(result['events']),2);self.assertEqual(result['version'],2)
   db.add(Match(job_id=j1.id,candidate_id=c.id,overall_score=50));db.commit()
   m=db.query(Match).first();m.overall_score=90;db.commit()
   self.assertEqual(history(j1.id,c.id,db,user)['stage'],'interview')
   self.assertEqual(len(history(j1.id,c.id,db,user)['events']),2)
   with self.assertRaises(HTTPException): change(j1.id,999,Change(stage='review',note='missing',version=0),db,user)
  engine.dispose()
if __name__=='__main__':unittest.main()
