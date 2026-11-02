"""Send synthetic telemetry through the running API and ask it for RUL predictions."""

import argparse
import logging
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd

logger = logging.getLogger("demo_pipeline")

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "ml" / "data_generator" / "generate_battery_data_v2.py"
TELEMETRY_CSV = REPO_ROOT / "data" / "synthetic" / "battery_telemetry_v2.csv"

SPLIT_SEED = 42
TRAIN_RATIO = 0.8
BATCH_SIZE = 5000
FIRST_PREDICTION_INDEX = 30
DEFAULT_HISTORY_STEP_DAYS = 30


def held_out_devices(device_ids: Iterable[str]) -> list[str]:
    """Reproduce the training split, so the demo only predicts for devices the model never saw."""
    shuffled = np.array(sorted(device_ids))
    np.random.default_rng(SPLIT_SEED).shuffle(shuffled)
    return sorted(shuffled[int(len(shuffled) * TRAIN_RATIO) :].tolist())


def to_reading(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "device_code": row["device_id"],
        "recorded_at": f"{row['date']}T00:00:00Z",
        "battery_level_pct": int(row["battery_level_pct"]),
        "battery_temp_c": float(row["battery_temperature_c"]),
        "voltage_mv": int(row["voltage_mv"]),
        # The generator does not simulate charging state and the model does not use it.
        "is_charging": False,
        "cycle_count": float(row["cycle_count"]),
        "deep_discharge_count": int(row["deep_discharge_count"]),
        "estimated_capacity_pct": round(float(row["soh_percent"]), 2),
        "source": "synthetic",
    }


class DemoPipeline:
    def __init__(self, client: httpx.Client, history_step_days: int) -> None:
        self._client = client
        self._history_step_days = history_step_days

    def run(self, telemetry: pd.DataFrame) -> None:
        self._ingest(telemetry)
        for position, (code, history) in enumerate(telemetry.groupby("device_id"), start=1):
            self._predict(code, sorted(history["date"].astype(str)))
            if position % 10 == 0:
                logger.info("predictions done devices=%s", position)

    def _ingest(self, telemetry: pd.DataFrame) -> None:
        records = telemetry.to_dict("records")
        for start in range(0, len(records), BATCH_SIZE):
            readings = [to_reading(row) for row in records[start : start + BATCH_SIZE]]
            response = self._client.post("/telemetry", json={"readings": readings})
            response.raise_for_status()
            logger.info("telemetry batch sent %s", response.json())

    def _predict(self, code: str, days: list[str]) -> None:
        predicted = self._client.get(f"/devices/{code}/predictions", params={"limit": 1000})
        predicted.raise_for_status()
        done = {item["telemetry_until"][:10] for item in predicted.json()}
        steps = days[FIRST_PREDICTION_INDEX :: self._history_step_days]
        if days[-1] not in steps:
            steps.append(days[-1])
        for day in steps:
            if day in done:
                continue
            response = self._client.post(
                f"/devices/{code}/predictions/run", params={"as_of": f"{day}T00:00:00Z"}
            )
            response.raise_for_status()


def load_telemetry() -> pd.DataFrame:
    if not TELEMETRY_CSV.exists():
        logger.info("generating synthetic telemetry")
        subprocess.run([sys.executable, str(GENERATOR)], check=True, stdout=subprocess.DEVNULL)
    telemetry = pd.read_csv(TELEMETRY_CSV)
    return telemetry[telemetry["device_id"].isin(held_out_devices(telemetry["device_id"].unique()))]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--history-step-days", type=int, default=DEFAULT_HISTORY_STEP_DAYS)
    args = parser.parse_args()

    with httpx.Client(base_url=args.api_url, timeout=120) as client:
        client.get("/health").raise_for_status()
        DemoPipeline(client, args.history_step_days).run(load_telemetry())
        logger.info("fleet summary %s", client.get("/predictions/summary").json())


if __name__ == "__main__":
    main()
