from fastapi import APIRouter, Depends

from app.core.security import require_recruiter_or_admin
from training.predict import SuitabilityPredictor

router = APIRouter()
predictor = SuitabilityPredictor()


@router.get("/status")
def model_status(current_user=Depends(require_recruiter_or_admin)):
    return {
        "model_available": predictor.available,
        "model_type": "RandomForestClassifier" if predictor.available else None,
        "model_name": "Candidate-Job Suitability Classifier",
        "classes": predictor.metadata.get("classes", ["HIGH", "MEDIUM", "LOW"]) if predictor.available else [],
        "feature_count": len(predictor.metadata.get("feature_names", [])) if predictor.available else 0,
        "model_version": predictor.metadata.get("model_version") if predictor.available else None,
        "prediction_mode": "trained-model" if predictor.available else "fallback",
    }
