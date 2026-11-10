import sys, os, unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['ENABLE_SENTENCE_TRANSFORMERS']='0'
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.database import Base
from app.api.routes.experiments import prepare, pairs, label, run, Label, Candidate, Job

class ExperimentsTest(unittest.TestCase):
    def test_annotation_and_comparison(self):
        engine=create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        user=SimpleNamespace(id=1,role='admin')
        with Session(engine) as db:
            db.add(Job(title='Python engineer',description='Python',required_skills=['Python'],status='open'))
            for n in range(5):
                db.add(Candidate(full_name=f'Test {n}',raw_text='Python',skills=['Python'],education={},projects=[],experience_years=1))
            db.commit()
            self.assertEqual(prepare(db,user)['created'],5)
            self.assertEqual(prepare(db,user)['created'],0)
            rows=pairs(db,user)
            with self.assertRaises(HTTPException): run(rows[0]['job_id'],db,user)
            for row in rows: label(row['id'],Label(relevance=2,notes='Meets Python requirement'),db,user)
            result=run(rows[0]['job_id'],db,user)
            self.assertEqual(result['tfidf']['ndcg@5'],1)
            self.assertIsNone(result['hybrid'])
            self.assertEqual(len(result['labels']),5)
        engine.dispose()
if __name__=='__main__': unittest.main()
