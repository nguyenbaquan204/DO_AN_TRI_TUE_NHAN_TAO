from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib

from app.services.skill_extractor import SkillExtractor
from training.feature_builder import FeatureBuilder

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "backend" / "models" / "candidate_job_suitability_model.joblib"
METADATA_PATH = ROOT / "backend" / "models" / "model_metadata.json"


class SuitabilityPredictor:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
        self.metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8")) if METADATA_PATH.exists() else {}
        self.builder = FeatureBuilder()

    @property
    def available(self) -> bool:
        return self.model is not None

    def predict(self, candidate_text: str, job_text: str, required_skills, preferred_skills=(), required_experience_years=0.0, education_required=None):
        if self.model is None:
            return None
        features = self.builder.build(
            candidate_text,
            job_text,
            SkillExtractor.extract(candidate_text),
            required_skills,
            preferred_skills,
            required_experience_years,
            education_required,
        )
        vector = self.builder.vector(features)
        predicted_class = str(self.model.predict(vector)[0])
        probabilities = self.model.predict_proba(vector)[0]
        confidence = float(max(probabilities))
        return {
            "predicted_class": predicted_class,
            "model_confidence": confidence,
            "model_version": self.metadata.get("model_version", "unknown"),
            "feature_snapshot": features,
        }
