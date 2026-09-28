from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.risk import RiskLevel

DEVICE_CODE_PATTERN = r"^DEV-\d{4,6}$"
DeviceCode = Annotated[str, Field(pattern=DEVICE_CODE_PATTERN, max_length=20)]


def to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class HealthOut(ApiModel):
    status: str


class TelemetryReadingIn(ApiModel):
    device_code: DeviceCode
    recorded_at: datetime
    battery_level_pct: int = Field(ge=0, le=100)
    battery_temp_c: Decimal = Field(ge=-40, le=120)
    voltage_mv: int = Field(gt=0)
    is_charging: bool
    cycle_count: int = Field(ge=0)
    estimated_capacity_pct: Decimal | None = Field(default=None, ge=0, le=100)
    ram_available_mb: int | None = Field(default=None, ge=0)
    network_rx_mb: Decimal | None = Field(default=None, ge=0)
    network_tx_mb: Decimal | None = Field(default=None, ge=0)
    source: Literal["synthetic", "real"] = "synthetic"

    @field_validator("recorded_at")
    @classmethod
    def _normalize_recorded_at(cls, value: datetime) -> datetime:
        return to_utc(value)


class TelemetryBatchIn(ApiModel):
    readings: list[TelemetryReadingIn] = Field(min_length=1, max_length=5000)


class IngestResult(ApiModel):
    inserted: int
    skipped: int


class TelemetryOut(ApiModel):
    recorded_at: datetime
    battery_level_pct: int
    battery_temp_c: Decimal
    voltage_mv: int
    is_charging: bool
    cycle_count: int
    estimated_capacity_pct: Decimal | None
    ram_available_mb: int | None
    network_rx_mb: Decimal | None
    network_tx_mb: Decimal | None
    source: str


class DeviceOut(ApiModel):
    code: str
    model: str | None
    os_version: str | None
    battery_design_capacity_mah: int | None
    is_active: bool
    enrolled_at: datetime


class ModelIn(ApiModel):
    name: str = Field(min_length=1, max_length=80)
    version: str = Field(min_length=1, max_length=40)
    algorithm: str = Field(min_length=1, max_length=80)
    target: str = Field(default="rul_cycles", max_length=40)
    trained_at: datetime
    training_rows: int | None = Field(default=None, ge=0)
    metrics: dict[str, Any] | None = None
    hyperparameters: dict[str, Any] | None = None
    features: list[str] | None = None
    artifact_path: str | None = Field(default=None, max_length=255)
    notes: str | None = None

    @field_validator("trained_at")
    @classmethod
    def _normalize_trained_at(cls, value: datetime) -> datetime:
        return to_utc(value)


class ModelOut(ModelIn):
    id: int


class PredictionIn(ApiModel):
    device_code: DeviceCode
    model_id: int
    rul_cycles: Decimal
    telemetry_until: datetime | None = None
    features: dict[str, Any] | None = None

    @field_validator("telemetry_until")
    @classmethod
    def _normalize_telemetry_until(cls, value: datetime | None) -> datetime | None:
        return None if value is None else to_utc(value)


class PredictionOut(ApiModel):
    id: int
    device_code: str
    model_id: int
    risk_policy_id: int | None
    predicted_at: datetime
    telemetry_until: datetime | None
    rul_cycles: Decimal
    risk_level: RiskLevel
    features: dict[str, Any] | None


class DeviceDetailOut(DeviceOut):
    latest_prediction: PredictionOut | None


class RiskSummaryOut(ApiModel):
    total_devices: int
    devices_with_prediction: int
    by_risk: dict[str, int]
