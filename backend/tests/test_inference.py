from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.config import get_settings
from app.features import FEATURES, REQUIRED_DAYS
from app.inference import JoblibRulPredictor, ModelUnavailableError, get_predictor
from app.models import RiskPolicy
from app.schemas import ModelIn
from tests.conftest import reading


class FakePredictor:
    def __init__(self, rul: float = 700.0) -> None:
        self.rul = rul
        self.calls: list[dict[str, float]] = []
        self.registration = ModelIn(
            name="battery-rul",
            version="fake",
            algorithm="RandomForestRegressor",
            trained_at=datetime(2026, 11, 1, tzinfo=UTC),
        )

    def predict(self, features: Mapping[str, float]) -> float:
        self.calls.append(dict(features))
        return self.rul


@pytest.fixture()
def predictor(client) -> FakePredictor:
    fake = FakePredictor()
    client.app.dependency_overrides[get_predictor] = lambda: fake
    return fake


def _daily_readings(code: str = "DEVICE-0001", days: int = REQUIRED_DAYS, skip: int | None = None):
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        reading(
            code,
            (start + timedelta(days=day)).isoformat(),
            cycle_count=round(day * 0.8, 2),
            estimated_capacity_pct=99.0 - day * 0.01,
        )
        for day in range(days)
        if day != skip
    ]


def _ingest(client, readings) -> None:
    response = client.post("/telemetry", json={"readings": readings})
    assert response.status_code == 201, response.text


def _run(client, code: str = "DEVICE-0001", **params):
    return client.post(f"/devices/{code}/predictions/run", params=params)


def test_run_persists_prediction_and_returns_risk(client, predictor):
    _ingest(client, _daily_readings(days=REQUIRED_DAYS + 4))

    response = _run(client)

    assert response.status_code == 201, response.text
    body = response.json()
    assert float(body["rul_cycles"]) == 700.0
    assert body["risk_level"] == "high"
    assert set(body["features"]) == set(FEATURES)
    assert body["telemetry_until"].startswith("2026-02-04")
    assert set(predictor.calls[0]) == set(FEATURES)

    history = client.get("/devices/DEVICE-0001/predictions").json()
    assert [item["id"] for item in history] == [body["id"]]


def test_run_rounds_rul_to_two_decimals(client, predictor):
    predictor.rul = 1234.56789
    _ingest(client, _daily_readings())
    assert float(_run(client).json()["rul_cycles"]) == 1234.57


def test_run_registers_the_model_only_once(client, predictor):
    _ingest(client, _daily_readings())
    first = _run(client).json()
    second = _run(client).json()
    assert first["model_id"] == second["model_id"]
    assert [model["version"] for model in client.get("/models").json()] == ["fake"]


def test_run_as_of_ignores_later_telemetry(client, predictor):
    _ingest(client, _daily_readings(days=REQUIRED_DAYS + 10))

    body = _run(client, as_of="2026-02-01T00:00:00Z").json()

    assert body["telemetry_until"].startswith("2026-02-01")
    assert body["features"]["observation_age_days"] == 31


def test_run_for_unknown_device_is_404(client, predictor):
    assert _run(client, "DEVICE-9999").status_code == 404


def test_run_with_short_history_is_422(client, predictor):
    _ingest(client, _daily_readings(days=20))

    response = _run(client)

    assert response.status_code == 422
    assert "20" in response.json()["detail"]
    assert client.get("/devices/DEVICE-0001/predictions").json() == []


def test_run_with_gap_in_window_is_422(client, predictor):
    _ingest(client, _daily_readings(days=REQUIRED_DAYS + 2, skip=REQUIRED_DAYS - 5))

    response = _run(client)

    assert response.status_code == 422
    assert "consecutive" in response.json()["detail"]


def test_run_without_model_artifact_is_503(client):
    def unavailable():
        raise ModelUnavailableError("model artifact not found")

    client.app.dependency_overrides[get_predictor] = unavailable
    _ingest(client, _daily_readings())

    response = _run(client)

    assert response.status_code == 503
    assert "not found" in response.json()["detail"]


def test_overview_joins_latest_reading_and_prediction(client, predictor):
    _ingest(client, _daily_readings("DEVICE-0001"))
    _ingest(client, [reading("DEVICE-0002", cycle_count=10.5)])
    _run(client, "DEVICE-0001")
    predictor.rul = 1200.0
    _run(client, "DEVICE-0001")

    rows = {row["code"]: row for row in client.get("/devices/overview").json()}

    assert set(rows) == {"DEVICE-0001", "DEVICE-0002"}
    first = rows["DEVICE-0001"]
    assert first["last_telemetry_at"].startswith("2026-01-31")
    assert float(first["estimated_capacity_pct"]) == pytest.approx(98.7)
    assert float(first["cycle_count"]) == 24.0
    assert float(first["latest_prediction"]["rul_cycles"]) == 1200.0
    assert first["latest_prediction"]["device_code"] == "DEVICE-0001"
    assert rows["DEVICE-0002"]["latest_prediction"] is None
    assert float(rows["DEVICE-0002"]["cycle_count"]) == 10.5


def test_overview_does_not_shadow_device_detail(client, predictor):
    _ingest(client, _daily_readings())
    assert client.get("/devices/DEVICE-0001").json()["code"] == "DEVICE-0001"
    assert client.get("/devices/overview").status_code == 200


def test_alerts_list_only_at_risk_devices_lowest_rul_first(client, predictor):
    for code, rul in (("DEVICE-0001", 900.0), ("DEVICE-0002", 700.0), ("DEVICE-0003", 1200.0)):
        _ingest(client, _daily_readings(code))
        predictor.rul = rul
        _run(client, code)

    alerts = client.get("/alerts").json()

    assert [(alert["device_code"], alert["risk_level"]) for alert in alerts] == [
        ("DEVICE-0002", "high"),
        ("DEVICE-0001", "medium"),
    ]
    assert alerts[0]["predicted_at"]
    assert alerts[0]["telemetry_until"].startswith("2026-01-31")


def test_alerts_follow_only_the_latest_prediction(client, predictor):
    _ingest(client, _daily_readings())
    _run(client)
    predictor.rul = 1200.0
    _run(client)
    assert client.get("/alerts").json() == []


def test_alerts_expose_the_policy_origin(client, predictor, session):
    session.add(
        RiskPolicy(
            name="experimental-v2",
            high_below_cycles=Decimal("776"),
            medium_below_cycles=Decimal("983"),
            source="experimental",
            is_active=True,
        )
    )
    session.commit()
    _ingest(client, _daily_readings())
    _run(client)

    alert = client.get("/alerts").json()[0]

    assert alert["policy_name"] == "experimental-v2"
    assert alert["policy_source"] == "experimental"
    assert float(alert["high_below_cycles"]) == 776
    assert float(alert["medium_below_cycles"]) == 983


def test_real_model_is_loaded_once_and_predicts_within_training_range():
    get_predictor.cache_clear()
    first = get_predictor()
    assert get_predictor() is first
    assert isinstance(first, JoblibRulPredictor)

    flat = {name: 1.0 for name in FEATURES}
    assert 497 <= first.predict(flat) <= 1764

    registration = first.registration
    assert registration.version == "RF-V2.2-TUNED"
    assert registration.features == list(FEATURES)
    assert registration.metrics["mae_cycles"] == pytest.approx(126.84, abs=0.01)
    assert set(registration.metrics["feature_importances"]) == set(FEATURES)
    assert registration.hyperparameters["max_depth"] == 8


def test_real_model_end_to_end_through_the_api(client):
    get_predictor.cache_clear()
    _ingest(client, _daily_readings(days=REQUIRED_DAYS + 5))

    body = _run(client).json()

    assert 497 <= float(body["rul_cycles"]) <= 1764
    assert client.get("/models").json()[0]["version"] == "RF-V2.2-TUNED"


def test_missing_artifact_raises_model_unavailable(tmp_path):
    metadata = get_settings().rul_metadata_path
    with pytest.raises(ModelUnavailableError):
        JoblibRulPredictor(tmp_path / "missing.joblib", metadata)
