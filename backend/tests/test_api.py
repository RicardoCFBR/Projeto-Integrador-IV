from datetime import UTC, datetime

from tests.conftest import reading


def _model_payload(version: str = "0.1.0") -> dict:
    return {
        "name": "battery-rul",
        "version": version,
        "algorithm": "RandomForestRegressor",
        "target": "rul_cycles",
        "trained_at": "2026-09-27T12:00:00Z",
        "training_rows": 36000,
        "metrics": {"mae": 12.4, "rmse": 17.8, "r2": 0.91},
        "hyperparameters": {"n_estimators": 200, "max_depth": 12},
        "features": ["temp_mean_7d", "cycle_count", "estimated_capacity_pct"],
    }


def _register_model(client) -> int:
    response = client.post("/models", json=_model_payload())
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_creates_device_and_reading(client):
    response = client.post("/telemetry", json={"readings": [reading()]})
    assert response.status_code == 201, response.text
    assert response.json() == {"inserted": 1, "skipped": 0}

    devices = client.get("/devices").json()
    assert [d["code"] for d in devices] == ["DEVICE-0001"]

    history = client.get("/devices/DEVICE-0001/telemetry").json()
    assert len(history) == 1
    assert history[0]["battery_level_pct"] == 78
    assert history[0]["source"] == "synthetic"


def test_ingest_duplicate_is_skipped(client):
    payload = {"readings": [reading()]}
    client.post("/telemetry", json=payload)
    response = client.post("/telemetry", json=payload)
    assert response.status_code == 201
    assert response.json() == {"inserted": 0, "skipped": 1}


def test_ingest_rejects_out_of_range_level(client):
    response = client.post("/telemetry", json={"readings": [reading(battery_level_pct=120)]})
    assert response.status_code == 422
    assert client.get("/devices").json() == []


def test_ingest_rejects_malformed_device_code(client):
    response = client.post("/telemetry", json={"readings": [reading(code="joao-silva")]})
    assert response.status_code == 422


def test_ingest_rejects_empty_batch(client):
    response = client.post("/telemetry", json={"readings": []})
    assert response.status_code == 422


def test_list_telemetry_since_and_descending(client):
    instants = ["2026-09-20T10:00:00Z", "2026-09-20T10:15:00Z", "2026-09-20T10:30:00Z"]
    client.post("/telemetry", json={"readings": [reading(recorded_at=t) for t in instants]})

    response = client.get("/devices/DEVICE-0001/telemetry", params={"since": instants[0]})
    assert response.status_code == 200
    returned = [_as_utc(item["recorded_at"]) for item in response.json()]
    assert returned == [_as_utc(instants[2]), _as_utc(instants[1])]

    limited = client.get("/devices/DEVICE-0001/telemetry", params={"limit": 1}).json()
    assert len(limited) == 1
    assert _as_utc(limited[0]["recorded_at"]) == _as_utc(instants[2])


def test_telemetry_for_unknown_device_is_404(client):
    assert client.get("/devices/DEVICE-9999/telemetry").status_code == 404


def test_register_model_and_list(client):
    model_id = _register_model(client)
    listed = client.get("/models").json()
    assert [m["id"] for m in listed] == [model_id]
    assert listed[0]["metrics"]["r2"] == 0.91


def test_model_name_and_version_are_unique(client):
    _register_model(client)
    response = client.post("/models", json=_model_payload())
    assert response.status_code == 409


def test_prediction_is_classified_by_active_policy(client):
    client.post("/telemetry", json={"readings": [reading()]})
    model_id = _register_model(client)
    expected = {"24": "high", "103": "medium", "284": "low"}
    for rul, level in expected.items():
        response = client.post(
            "/predictions",
            json={
                "device_code": "DEVICE-0001",
                "model_id": model_id,
                "rul_cycles": rul,
                "telemetry_until": "2026-09-20T10:00:00Z",
                "features": {"cycle_count": 184},
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["risk_level"] == level
        assert body["device_code"] == "DEVICE-0001"
        assert body["model_id"] == model_id

    history = client.get("/devices/DEVICE-0001/predictions").json()
    assert [p["risk_level"] for p in history] == ["low", "medium", "high"]


def test_prediction_for_unknown_device_is_404(client):
    model_id = _register_model(client)
    response = client.post(
        "/predictions",
        json={"device_code": "DEVICE-9999", "model_id": model_id, "rul_cycles": "10"},
    )
    assert response.status_code == 404


def test_prediction_for_unknown_model_is_404(client):
    client.post("/telemetry", json={"readings": [reading()]})
    response = client.post(
        "/predictions",
        json={"device_code": "DEVICE-0001", "model_id": 999, "rul_cycles": "10"},
    )
    assert response.status_code == 404


def test_summary_uses_latest_prediction_per_device(client):
    client.post(
        "/telemetry",
        json={"readings": [reading("DEVICE-0001"), reading("DEVICE-0002"), reading("DEVICE-0003")]},
    )
    model_id = _register_model(client)

    def predict(code: str, rul: str) -> None:
        response = client.post(
            "/predictions", json={"device_code": code, "model_id": model_id, "rul_cycles": rul}
        )
        assert response.status_code == 201, response.text

    predict("DEVICE-0001", "24")
    predict("DEVICE-0001", "284")
    predict("DEVICE-0002", "103")

    summary = client.get("/predictions/summary").json()
    assert summary == {
        "total_devices": 3,
        "devices_with_prediction": 2,
        "by_risk": {"low": 1, "medium": 1, "high": 0},
    }


def test_device_detail_includes_latest_prediction(client):
    client.post("/telemetry", json={"readings": [reading()]})
    model_id = _register_model(client)
    client.post(
        "/predictions", json={"device_code": "DEVICE-0001", "model_id": model_id, "rul_cycles": "24"}
    )
    client.post(
        "/predictions", json={"device_code": "DEVICE-0001", "model_id": model_id, "rul_cycles": "284"}
    )
    detail = client.get("/devices/DEVICE-0001").json()
    assert detail["code"] == "DEVICE-0001"
    assert detail["latest_prediction"]["risk_level"] == "low"

    assert client.get("/devices/DEVICE-9999").status_code == 404


def _as_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
