import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['ENABLE_SENTENCE_TRANSFORMERS'] = '0'

from app.ai.matching_engine import MatchingEngine
from app.services.matching_inputs import candidate_inputs, resolve_requirements
from training.predict import SuitabilityPredictor


class ReviewedMatchingTests(unittest.TestCase):
    def profile(self, **changes):
        values = dict(raw_text='Python 10 years experience Master built project',
                      skills=[], experience_years=1, education={}, work_experience={},
                      projects=[], certificates=[], languages=[])
        values.update(changes)
        return SimpleNamespace(**values)

    def test_reviewed_fields_replace_raw_ocr(self):
        inputs = candidate_inputs(self.profile())
        result = MatchingEngine().score_candidate(**inputs, jd_text='Python developer',
            required_skills=['Python'], required_experience_years=5,
            education_required='Master', use_semantic=False)
        self.assertEqual(result['experience_score'], 20)
        self.assertEqual(result['education_score'], 0)
        self.assertEqual(result['skill_score'], 0)
        self.assertEqual(result['project_score'], 0)
        self.assertNotIn('Master', inputs['cv_text'])

    def test_zero_years_is_authoritative(self):
        inputs = candidate_inputs(self.profile(experience_years=0, work_experience={'text': '10 years experience'}))
        score = MatchingEngine().score_candidate(**inputs, jd_text='Engineer', required_skills=[], required_experience_years=5, use_semantic=False)
        self.assertEqual(score['experience_score'], 0)

    def test_empty_profile_cannot_get_seventy_points(self):
        score = MatchingEngine().score_candidate('', '', [], [], use_semantic=False)
        self.assertEqual(score['overall_score'], 0)
        self.assertEqual(score['data_status'], 'insufficient-data')

    def test_vietnamese_degree(self):
        self.assertEqual(MatchingEngine._education_score('Tốt nghiệp đại học', 'Đại học'), 100)
        self.assertLess(MatchingEngine._education_score('Cao đẳng', 'Đại học'), 100)

    def test_cleared_job_requirements_do_not_return(self):
        job = SimpleNamespace(required_skills=[], preferred_skills=[], experience_required='0',
                              education_required='', education_level='Master')
        result = resolve_requirements(job, {'experience_years': 10, 'education_required': 'Master'})
        self.assertEqual(result['required_experience_years'], 0)
        self.assertEqual(result['education_required'], '')

    def test_classifier_uses_reviewed_skills(self):
        predictor = SuitabilityPredictor()
        predictor.builder.semantic_enabled = False
        result = predictor.predict('Python 10 years Master', 'Python engineer', ['Python'],
            candidate_skills=[], feature_overrides={'candidate_experience_years': 1.0})
        self.assertIsNotNone(result)
        self.assertEqual(result['feature_snapshot']['required_skill_matched_count'], 0)
        self.assertEqual(result['feature_snapshot']['candidate_experience_years'], 1)

    def test_api_persists_reviewed_score_in_isolated_database(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from app.core.database import Base
        from app.models.resume import Resume
        from app.models.match_detail import MatchDetail
        from app.models.candidate import Candidate
        from app.models.job import Job
        from app.api.routes.matching import create_match
        database = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(database)
        with Session(database) as db:
            candidate = Candidate(full_name='Regression fixture', **vars(self.profile()))
            job = Job(title='Engineer', description='Python engineer', required_skills=['Python'],
                      preferred_skills=[], experience_required='5 years', education_required='Master')
            db.add_all([candidate, job])
            db.commit()
            result = create_match(job.id, candidate.id, db, SimpleNamespace(role='admin'))
            self.assertEqual(result['experience_score'], 20)
            self.assertEqual(result['skill_score'], 0)
            self.assertEqual(result['feature_snapshot']['candidate_experience_years'], 1)
            self.assertEqual(result['feature_snapshot']['required_skill_matched_count'], 0)
            self.assertEqual(result['feature_snapshot']['scoring_version'], 'reviewed-profile-v2')
        database.dispose()


if __name__ == '__main__':
    unittest.main()
