from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.database import Base
from app.models import BatteryPrediction, BatteryTelemetry, Device, MlModel, RiskPolicy
from app.repositories import (
    DeviceRepository,
    PredictionRepository,
    TelemetryRepository,
)
from app.risk import RiskLevel
from app.schemas import TelemetryReadingIn
from tests.conftest import reading

EXPECTED_TABLES = {"device", "battery_telemetry", "ml_model", "risk_policy", "battery_prediction"}


def test_metadata_declares_exactly_the_five_tables():
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_device_code_is_unique(session):
    session.add(Device(code="DEVICE-0001"))
    session.commit()
    session.add(Device(code="DEVICE-0001"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_telemetry_is_unique_per_device_and_instant(session):
    device = Device(code="DEVICE-0001")
    session.add(device)
    session.flush()
    instant = datetime(2026, 9, 20, 10, 0, tzinfo=UTC)
    common = dict(
        device_id=device.id,
        recorded_at=instant,
        battery_level_pct=80,
        battery_temp_c=Decimal("30.5"),
        voltage_mv=3900,
        is_charging=False,
        cycle_count=10,
    )
    session.add(BatteryTelemetry(**common))
    session.commit()
    session.add(BatteryTelemetry(**common))
    with pytest.raises(IntegrityError):
        session.commit()


def test_telemetry_source_defaults_to_synthetic(session):
    device = Device(code="DEVICE-0001")
    session.add(device)
    session.flush()
    row = BatteryTelemetry(
        device_id=device.id,
        recorded_at=datetime(2026, 9, 20, 10, 0, tzinfo=UTC),
        battery_level_pct=80,
        battery_temp_c=Decimal("30.5"),
        voltage_mv=3900,
        is_charging=False,
        cycle_count=10,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    assert row.source == "synthetic"


def test_device_repository_get_or_create_is_idempotent(session):
    repo = DeviceRepository(session)
    first = repo.get_or_create("DEVICE-0042")
    second = repo.get_or_create("DEVICE-0042")
    session.commit()
    assert first.id == second.id
    assert len(repo.list()) == 1


def test_bulk_insert_registers_devices_and_skips_duplicates(session):
    repo = TelemetryRepository(session)
    batch = [
        TelemetryReadingIn(**reading("DEVICE-0001", "2026-09-20T10:00:00Z")),
        TelemetryReadingIn(**reading("DEVICE-0001", "2026-09-20T10:15:00Z")),
        TelemetryReadingIn(**reading("DEVICE-0002", "2026-09-20T10:00:00Z")),
        TelemetryReadingIn(**reading("DEVICE-0002", "2026-09-20T10:00:00Z")),
    ]
    result = repo.bulk_insert(batch)
    session.commit()
    assert (result.inserted, result.skipped) == (3, 1)

    again = repo.bulk_insert(batch[:3])
    session.commit()
    assert (again.inserted, again.skipped) == (0, 3)
    assert len(DeviceRepository(session).list()) == 2


def test_prediction_links_device_model_and_policy(session):
    device = Device(code="DEVICE-0001")
    model = MlModel(
        name="battery-rul",
        version="0.1.0",
        algorithm="RandomForestRegressor",
        target="rul_cycles",
        trained_at=datetime(2026, 9, 27, 12, 0, tzinfo=UTC),
    )
    policy = RiskPolicy(
        name="experimental-v1",
        high_below_cycles=Decimal("50"),
        medium_below_cycles=Decimal("150"),
        is_active=True,
    )
    session.add_all([device, model, policy])
    session.flush()

    prediction = PredictionRepository(session).create(
        device=device,
        model=model,
        rul_cycles=Decimal("24"),
        features={"temp_mean_7d": 38.4},
        telemetry_until=None,
    )
    session.commit()
    session.refresh(prediction)
    assert isinstance(prediction, BatteryPrediction)
    assert prediction.risk_level is RiskLevel.HIGH
    assert prediction.risk_policy_id == policy.id
    assert prediction.features == {"temp_mean_7d": 38.4}


def test_only_one_risk_policy_can_be_active(session):
    session.add(
        RiskPolicy(
            name="a",
            high_below_cycles=Decimal("50"),
            medium_below_cycles=Decimal("150"),
            is_active=True,
        )
    )
    session.commit()
    session.add(
        RiskPolicy(
            name="b",
            high_below_cycles=Decimal("60"),
            medium_below_cycles=Decimal("160"),
            is_active=True,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
