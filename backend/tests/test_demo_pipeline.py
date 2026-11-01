import csv
from pathlib import Path

import pandas as pd
import pytest

from app.inference import get_predictor
from scripts.run_demo_pipeline import DemoPipeline, held_out_devices, to_reading
from tests.test_inference import FakePredictor

FIXTURES = Path(__file__).parent / "fixtures"
DEVICE = "DEVICE-0002"


@pytest.fixture()
def telemetry() -> pd.DataFrame:
    with (FIXTURES / "device_history.csv").open(encoding="utf-8") as file:
        frame = pd.DataFrame(list(csv.DictReader(file)))
    frame["device_id"] = DEVICE
    frame["soh_percent"] = "97.1234"
    return frame.head(60)


def test_held_out_devices_match_the_training_split():
    devices = [f"DEVICE-{number:04d}" for number in range(1, 401)]
    held_out = held_out_devices(devices)
    assert len(held_out) == 80
    assert held_out == sorted(held_out)
    assert DEVICE in held_out
    assert held_out == held_out_devices(list(reversed(devices)))


def test_to_reading_declares_synthetic_source_and_rounds_capacity():
    row = {
        "device_id": DEVICE,
        "date": "2026-01-31",
        "battery_temperature_c": "33.1",
        "battery_level_pct": "77",
        "voltage_mv": "4000",
        "cycle_count": "12.34",
        "deep_discharge_count": "2",
        "soh_percent": "97.1234",
    }
    reading = to_reading(row)
    assert reading == {
        "device_code": DEVICE,
        "recorded_at": "2026-01-31T00:00:00Z",
        "battery_level_pct": 77,
        "battery_temp_c": 33.1,
        "voltage_mv": 4000,
        "is_charging": False,
        "cycle_count": 12.34,
        "deep_discharge_count": 2,
        "estimated_capacity_pct": 97.12,
        "source": "synthetic",
    }


def test_pipeline_ingests_and_predicts_at_each_step(client, telemetry):
    client.app.dependency_overrides[get_predictor] = FakePredictor

    DemoPipeline(client, history_step_days=10).run(telemetry)

    assert len(client.get(f"/devices/{DEVICE}/telemetry", params={"limit": 500}).json()) == 60
    predictions = client.get(f"/devices/{DEVICE}/predictions").json()
    days = sorted(item["telemetry_until"][:10] for item in predictions)
    assert days == ["2026-01-31", "2026-02-10", "2026-02-20", "2026-03-01"]
    assert predictions[0]["telemetry_until"].startswith("2026-03-01")


def test_pipeline_rerun_adds_nothing(client, telemetry):
    client.app.dependency_overrides[get_predictor] = FakePredictor
    pipeline = DemoPipeline(client, history_step_days=10)

    pipeline.run(telemetry)
    pipeline.run(telemetry)

    assert len(client.get(f"/devices/{DEVICE}/predictions").json()) == 4
