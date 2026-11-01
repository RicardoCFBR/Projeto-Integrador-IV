import json
import logging
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Protocol

import joblib
import pandas as pd

from app.config import get_settings
from app.features import FEATURES
from app.schemas import ModelIn

logger = logging.getLogger(__name__)

MODEL_NAME = "battery-rul"
MODEL_VERSION = "RF-V2.2-TUNED"
MODEL_ALGORITHM = "RandomForestRegressor"
MODEL_NOTES = "Trained and evaluated only on synthetic data; not validated with real telemetry."


class ModelUnavailableError(RuntimeError):
    pass


class RulPredictor(Protocol):
    registration: ModelIn

    def predict(self, features: Mapping[str, float]) -> float: ...


class JoblibRulPredictor:
    """Serves the versioned Random Forest. Only load artifacts from this repository."""

    def __init__(self, model_path: Path, metadata_path: Path) -> None:
        if not model_path.exists() or not metadata_path.exists():
            raise ModelUnavailableError(f"model artifact not found at {model_path.name}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if tuple(metadata["features"]) != FEATURES:
            raise ModelUnavailableError("model features differ from the inference contract")

        self._model = joblib.load(model_path)
        # A single row gains nothing from the worker pool saved with the training settings.
        self._model.n_jobs = 1
        self.registration = self._build_registration(metadata, model_path)
        logger.info("rul model loaded version=%s", MODEL_VERSION)

    def predict(self, features: Mapping[str, float]) -> float:
        row = pd.DataFrame([dict(features)], columns=list(FEATURES))
        return float(self._model.predict(row)[0])

    def _build_registration(self, metadata: dict, model_path: Path) -> ModelIn:
        importances = dict(zip(FEATURES, self._model.feature_importances_.tolist(), strict=True))
        return ModelIn(
            name=MODEL_NAME,
            version=MODEL_VERSION,
            algorithm=MODEL_ALGORITHM,
            target=metadata["target"],
            trained_at=metadata["trained_at"],
            training_rows=metadata["dataset"]["development_rows"],
            metrics={**metadata["test_metrics"], "feature_importances": importances},
            hyperparameters=metadata["search"]["best_params"],
            features=list(FEATURES),
            artifact_path=f"ml/artifacts/{model_path.parent.name}/{model_path.name}",
            notes=MODEL_NOTES,
        )


@lru_cache
def get_predictor() -> RulPredictor:
    settings = get_settings()
    return JoblibRulPredictor(settings.rul_model_path, settings.rul_metadata_path)
