from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.risk import RiskLevel

BigIntPk = BigInteger().with_variant(Integer(), "sqlite")
JsonDoc = JSON().with_variant(JSONB(), "postgresql")
TzTimestamp = DateTime(timezone=True)

TELEMETRY_SOURCES = ("synthetic", "real")
POLICY_SOURCES = ("experimental", "community", "literature")


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Device(Base):
    """A fleet handset identified only by a pseudonymous code."""

    __tablename__ = "device"
    __table_args__ = (
        CheckConstraint("battery_design_capacity_mah > 0", name="ck_device_capacity_positive"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    model: Mapped[str | None] = mapped_column(String(80))
    os_version: Mapped[str | None] = mapped_column(String(40))
    battery_design_capacity_mah: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        TzTimestamp, nullable=False, default=_utc_now, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        TzTimestamp, nullable=False, default=_utc_now, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TzTimestamp,
        nullable=False,
        default=_utc_now,
        onupdate=_utc_now,
        server_default=func.now(),
    )

    telemetry: Mapped[list["BatteryTelemetry"]] = relationship(
        back_populates="device", cascade="all, delete-orphan", passive_deletes=True
    )
    predictions: Mapped[list["BatteryPrediction"]] = relationship(
        back_populates="device", cascade="all, delete-orphan", passive_deletes=True
    )


class BatteryTelemetry(Base):
    """One battery reading of one device at one instant."""

    __tablename__ = "battery_telemetry"
    __table_args__ = (
        UniqueConstraint("device_id", "recorded_at", name="uq_battery_telemetry_device_instant"),
        CheckConstraint(
            "battery_level_pct BETWEEN 0 AND 100", name="ck_battery_telemetry_level_range"
        ),
        CheckConstraint("voltage_mv > 0", name="ck_battery_telemetry_voltage_positive"),
        CheckConstraint("cycle_count >= 0", name="ck_battery_telemetry_cycles_non_negative"),
        CheckConstraint(
            "estimated_capacity_pct BETWEEN 0 AND 100",
            name="ck_battery_telemetry_capacity_range",
        ),
        CheckConstraint("ram_available_mb >= 0", name="ck_battery_telemetry_ram_non_negative"),
        CheckConstraint("network_rx_mb >= 0", name="ck_battery_telemetry_rx_non_negative"),
        CheckConstraint("network_tx_mb >= 0", name="ck_battery_telemetry_tx_non_negative"),
        CheckConstraint(
            "source IN ('synthetic', 'real')", name="ck_battery_telemetry_source_allowed"
        ),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("device.id", ondelete="CASCADE"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(TzTimestamp, nullable=False)
    battery_level_pct: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    battery_temp_c: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    voltage_mv: Mapped[int] = mapped_column(Integer, nullable=False)
    is_charging: Mapped[bool] = mapped_column(Boolean, nullable=False)
    cycle_count: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_capacity_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    ram_available_mb: Mapped[int | None] = mapped_column(Integer)
    network_rx_mb: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    network_tx_mb: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    source: Mapped[str] = mapped_column(
        String(10), nullable=False, default="synthetic", server_default="synthetic"
    )
    ingested_at: Mapped[datetime] = mapped_column(
        TzTimestamp, nullable=False, default=_utc_now, server_default=func.now()
    )

    device: Mapped[Device] = relationship(back_populates="telemetry")


Index(
    "ix_battery_telemetry_device_recorded_desc",
    BatteryTelemetry.device_id,
    BatteryTelemetry.recorded_at.desc(),
)


class MlModel(Base):
    """A trained model version and the metrics observed at training time."""

    __tablename__ = "ml_model"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_ml_model_name_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(80), nullable=False)
    target: Mapped[str] = mapped_column(
        String(40), nullable=False, default="rul_cycles", server_default="rul_cycles"
    )
    trained_at: Mapped[datetime] = mapped_column(TzTimestamp, nullable=False)
    training_rows: Mapped[int | None] = mapped_column(Integer)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JsonDoc)
    hyperparameters: Mapped[dict[str, Any] | None] = mapped_column(JsonDoc)
    features: Mapped[list[str] | None] = mapped_column(JsonDoc)
    artifact_path: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TzTimestamp, nullable=False, default=_utc_now, server_default=func.now()
    )

    predictions: Mapped[list["BatteryPrediction"]] = relationship(back_populates="model")


class RiskPolicy(Base):
    """Thresholds, in cycles, that turn an RUL estimate into a risk band."""

    __tablename__ = "risk_policy"
    __table_args__ = (
        CheckConstraint("high_below_cycles > 0", name="ck_risk_policy_high_positive"),
        CheckConstraint(
            "medium_below_cycles > high_below_cycles", name="ck_risk_policy_threshold_order"
        ),
        CheckConstraint(
            "source IN ('experimental', 'community', 'literature')",
            name="ck_risk_policy_source_allowed",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    high_below_cycles: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    medium_below_cycles: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="experimental", server_default="experimental"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TzTimestamp, nullable=False, default=_utc_now, server_default=func.now()
    )


Index(
    "ux_risk_policy_single_active",
    RiskPolicy.is_active,
    unique=True,
    postgresql_where=text("is_active"),
    sqlite_where=text("is_active"),
)


class BatteryPrediction(Base):
    """An RUL estimate for one device produced by one model version."""

    __tablename__ = "battery_prediction"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("device.id", ondelete="CASCADE"), nullable=False
    )
    model_id: Mapped[int] = mapped_column(ForeignKey("ml_model.id"), nullable=False)
    risk_policy_id: Mapped[int | None] = mapped_column(ForeignKey("risk_policy.id"))
    predicted_at: Mapped[datetime] = mapped_column(
        TzTimestamp, nullable=False, default=_utc_now, server_default=func.now()
    )
    telemetry_until: Mapped[datetime | None] = mapped_column(TzTimestamp)
    rul_cycles: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(
            RiskLevel,
            name="risk_level",
            native_enum=False,
            length=10,
            create_constraint=True,
            values_callable=lambda members: [member.value for member in members],
        ),
        nullable=False,
    )
    features: Mapped[dict[str, Any] | None] = mapped_column(JsonDoc)

    device: Mapped[Device] = relationship(back_populates="predictions")
    model: Mapped[MlModel] = relationship(back_populates="predictions")
    risk_policy: Mapped[RiskPolicy | None] = relationship()

    @property
    def device_code(self) -> str:
        return self.device.code


Index(
    "ix_battery_prediction_device_predicted_desc",
    BatteryPrediction.device_id,
    BatteryPrediction.predicted_at.desc(),
)
