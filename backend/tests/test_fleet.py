import pytest

from tests.conftest import reading


def _ingest(client, *readings) -> None:
    response = client.post("/telemetry", json={"readings": list(readings)})
    assert response.status_code == 201, response.text


def test_trend_averages_capacity_per_day_oldest_first(client):
    _ingest(
        client,
        reading("DEVICE-0001", "2026-03-02T00:00:00Z", estimated_capacity_pct=89.0),
        reading("DEVICE-0001", "2026-03-01T00:00:00Z", estimated_capacity_pct=90.0),
        reading("DEVICE-0002", "2026-03-01T00:00:00Z", estimated_capacity_pct=94.0),
    )

    trend = client.get("/fleet/trend").json()

    assert [point["day"] for point in trend] == ["2026-03-01", "2026-03-02"]
    assert trend[0]["soh_percent"] == pytest.approx(92.0)
    assert trend[1]["soh_percent"] == pytest.approx(89.0)


def test_trend_keeps_only_the_latest_days(client):
    _ingest(
        client,
        reading("DEVICE-0001", "2026-03-01T00:00:00Z"),
        reading("DEVICE-0001", "2026-03-02T00:00:00Z"),
    )
    trend = client.get("/fleet/trend", params={"days": 1}).json()
    assert [point["day"] for point in trend] == ["2026-03-02"]


def test_trend_skips_days_reported_by_a_small_part_of_the_fleet(client):
    _ingest(
        client,
        reading("DEVICE-0001", "2026-03-01T00:00:00Z", estimated_capacity_pct=90.0),
        reading("DEVICE-0002", "2026-03-01T00:00:00Z", estimated_capacity_pct=90.0),
        reading("DEVICE-0003", "2026-03-01T00:00:00Z", estimated_capacity_pct=90.0),
        reading("DEVICE-0001", "2026-03-02T00:00:00Z", estimated_capacity_pct=99.0),
    )
    trend = client.get("/fleet/trend").json()
    assert [point["day"] for point in trend] == ["2026-03-01"]


def test_trend_ignores_readings_without_capacity(client):
    _ingest(client, reading("DEVICE-0001", estimated_capacity_pct=None))
    assert client.get("/fleet/trend").json() == []
