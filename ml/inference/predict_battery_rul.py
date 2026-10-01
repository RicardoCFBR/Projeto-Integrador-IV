from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

MODEL_VERSION = "RF-V2.2-TUNED"

FEATURES = [
    "cycle_count",
    "temperature_mean_7d",
    "temperature_max_7d",
    "temperature_std_7d",
    "temperature_mean_30d",
    "temperature_std_30d",
    "hot_days_30d",
    "daily_cycles_mean_7d",
    "daily_cycles_std_7d",
    "daily_cycles_mean_30d",
    "daily_cycles_std_30d",
    "deep_discharge_events_30d",
    "cycle_count_change_30d",
    "battery_level_mean_7d",
    "voltage_mean_7d",
    "voltage_std_7d",
    "observation_age_days",
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "artifacts"
    / "v2_2_tuned"
    / "battery_rul_random_forest_v2_2_tuned.joblib"
)
DEFAULT_METADATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "artifacts"
    / "v2_2_tuned"
    / "battery_rul_random_forest_v2_2_tuned_metadata.json"
)


def load_model(model_path: Path = DEFAULT_MODEL_PATH):
    """Load the trained Random Forest artifact from a trusted local path."""
    if not model_path.exists():
        raise FileNotFoundError(
            "Modelo não encontrado em: "
            f"{model_path}. Gere/restaure o artefato local antes da inferência."
        )
    return joblib.load(model_path)


def load_metadata(metadata_path: Path = DEFAULT_METADATA_PATH) -> dict[str, Any] | None:
    if not metadata_path.exists():
        return None

    with metadata_path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    metadata_features = metadata.get("features")
    if metadata_features is not None and metadata_features != FEATURES:
        raise ValueError(
            "A ordem/lista de features do metadata não corresponde ao contrato "
            "de inferência V2.2."
        )

    return metadata


def validate_features(feature_data: dict[str, Any]) -> dict[str, float]:
    missing = [feature for feature in FEATURES if feature not in feature_data]
    if missing:
        raise ValueError(
            "Features obrigatórias ausentes: " + ", ".join(missing)
        )

    validated: dict[str, float] = {}

    for feature in FEATURES:
        value = feature_data[feature]

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(
                f"A feature '{feature}' deve ser numérica. "
                f"Valor recebido: {value!r}"
            )

        numeric_value = float(value)

        if not np.isfinite(numeric_value):
            raise ValueError(
                f"A feature '{feature}' deve ser finita. "
                f"Valor recebido: {value!r}"
            )

        validated[feature] = numeric_value

    return validated


def predict_rul(
    feature_data: dict[str, Any],
    device_id: str | None = None,
    model_path: Path = DEFAULT_MODEL_PATH,
) -> dict[str, Any]:
    validated = validate_features(feature_data)
    model = load_model(model_path)

    input_df = pd.DataFrame([validated], columns=FEATURES)
    prediction = float(model.predict(input_df)[0])

    result: dict[str, Any] = {
        "predicted_rul_cycles": round(prediction, 2),
        "model_version": MODEL_VERSION,
        "feature_count": len(FEATURES),
    }

    if device_id:
        result["device_id"] = device_id

    return result


def load_request(input_path: Path) -> tuple[str | None, dict[str, Any]]:
    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_path}")

    with input_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        raise TypeError("O JSON de entrada deve conter um objeto.")

    device_id = payload.get("device_id")
    features = payload.get("features")

    if features is None:
        features = {
            key: value
            for key, value in payload.items()
            if key != "device_id"
        }

    if not isinstance(features, dict):
        raise TypeError("O campo 'features' deve ser um objeto JSON.")

    return device_id, features


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Executa inferência de RUL usando o Random Forest V2.2 Tuned."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Caminho para um JSON contendo device_id e as 17 features.",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help="Caminho opcional para o arquivo .joblib do modelo.",
    )

    args = parser.parse_args()

    load_metadata()
    device_id, features = load_request(args.input)
    result = predict_rul(
        feature_data=features,
        device_id=device_id,
        model_path=args.model,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
