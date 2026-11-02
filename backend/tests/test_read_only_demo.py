"""Cloud demo: real prediction previews, no database writes."""
from datetime import UTC, datetime, timedelta

from app.inference import get_predictor
from app.main import create_app
from tests.conftest import reading
from tests.test_inference import FakePredictor


def test_public_demo_blocks_every_write_method():
    from fastapi.testclient import TestClient
    from app.main import ReadOnlyDemoMiddleware
    app = create_app()
    app.add_middleware(ReadOnlyDemoMiddleware)
    with TestClient(app) as client:
        for method, route in (
        ("POST", "/telemetry"),
        ("POST", "/models"),
        ("POST", "/predictions"),
        ("POST", "/devices/DEVICE-0001/predictions/run"),
        ("PUT", "/telemetry"),
        ("PATCH", "/telemetry"),
        ("DELETE", "/telemetry"),
        ):
            response = client.request(method, route)
            assert response.status_code == 403, (method, route, response.text)


def test_preview_does_not_persist_prediction(client):
    fake = FakePredictor(rul=903.0)
    client.app.dependency_overrides[get_predictor] = lambda: fake
    start = datetime(2026, 1, 1, tzinfo=UTC)
    readings = [
        reading("DEVICE-0001", (start + timedelta(days=day)).isoformat(), cycle_count=day)
        for day in range(31)
    ]
    assert client.post("/telemetry", json={"readings": readings}).status_code == 201
    before = client.get("/devices/DEVICE-0001/predictions").json()
    assert before == []
    preview = client.get("/devices/DEVICE-0001/predictions/preview")
    assert preview.status_code == 200, preview.text
    assert preview.json()["persisted"] is False
    assert float(preview.json()["rul_cycles"]) == 903.0
    assert preview.json()["risk_level"] == "medium"
    assert client.get("/devices/DEVICE-0001/predictions").json() == []
    assert client.get("/models").json() == []
