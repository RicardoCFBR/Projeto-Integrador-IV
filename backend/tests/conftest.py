from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_session
from app.main import create_app


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture()
def session(session_factory) -> Iterator[Session]:
    with session_factory() as db:
        yield db


@pytest.fixture()
def client(session_factory) -> Iterator[TestClient]:
    app = create_app()

    def override() -> Iterator[Session]:
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_session] = override
    with TestClient(app) as test_client:
        yield test_client


def reading(code: str = "DEV-0001", recorded_at: str = "2026-09-20T10:00:00Z", **overrides):
    payload = {
        "device_code": code,
        "recorded_at": recorded_at,
        "battery_level_pct": 78,
        "battery_temp_c": 31.2,
        "voltage_mv": 3900,
        "is_charging": False,
        "cycle_count": 184,
        "estimated_capacity_pct": 94.0,
        "ram_available_mb": 1536,
        "network_rx_mb": 12.5,
        "network_tx_mb": 3.25,
    }
    payload.update(overrides)
    return payload
