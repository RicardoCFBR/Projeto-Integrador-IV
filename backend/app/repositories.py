from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import BatteryPrediction, BatteryTelemetry, Device, MlModel, RiskPolicy
from app.risk import RiskClassifier, RiskLevel
from app.schemas import IngestResult, ModelIn, RiskSummaryOut, TelemetryReadingIn, to_utc


class NotFoundError(LookupError):
    pass


class ConflictError(RuntimeError):
    pass


def _instant_key(value: datetime) -> datetime:
    """Normalize to naive UTC so values from SQLite and PostgreSQL compare equal."""
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_code(self, code: str) -> Device | None:
        return self._session.scalar(select(Device).where(Device.code == code))

    def require(self, code: str) -> Device:
        device = self.get_by_code(code)
        if device is None:
            raise NotFoundError(f"device {code} not found")
        return device

    def get_or_create(self, code: str) -> Device:
        device = self.get_by_code(code)
        if device is None:
            device = Device(code=code)
            self._session.add(device)
            self._session.flush()
        return device

    def list(self) -> list[Device]:
        return list(self._session.scalars(select(Device).order_by(Device.code)))

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(Device)) or 0


class TelemetryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def bulk_insert(self, readings: Sequence[TelemetryReadingIn]) -> IngestResult:
        devices = DeviceRepository(self._session)
        grouped: dict[str, list[TelemetryReadingIn]] = defaultdict(list)
        for item in readings:
            grouped[item.device_code].append(item)

        inserted = skipped = 0
        for code, items in grouped.items():
            device = devices.get_or_create(code)
            existing = self._existing_instants(device.id, items)
            for item in items:
                key = _instant_key(item.recorded_at)
                if key in existing:
                    skipped += 1
                    continue
                existing.add(key)
                self._session.add(
                    BatteryTelemetry(
                        device_id=device.id, **item.model_dump(exclude={"device_code"})
                    )
                )
                inserted += 1
        self._session.flush()
        return IngestResult(inserted=inserted, skipped=skipped)

    def _existing_instants(
        self, device_id: int, items: Sequence[TelemetryReadingIn]
    ) -> set[datetime]:
        instants = [item.recorded_at for item in items]
        stmt = select(BatteryTelemetry.recorded_at).where(
            BatteryTelemetry.device_id == device_id,
            BatteryTelemetry.recorded_at >= min(instants),
            BatteryTelemetry.recorded_at <= max(instants),
        )
        return {_instant_key(value) for value in self._session.scalars(stmt)}

    def list_for_device(
        self, device: Device, since: datetime | None = None, limit: int = 100
    ) -> list[BatteryTelemetry]:
        stmt = select(BatteryTelemetry).where(BatteryTelemetry.device_id == device.id)
        if since is not None:
            stmt = stmt.where(BatteryTelemetry.recorded_at > to_utc(since))
        stmt = stmt.order_by(BatteryTelemetry.recorded_at.desc()).limit(limit)
        return list(self._session.scalars(stmt))


class ModelRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, model_id: int) -> MlModel | None:
        return self._session.get(MlModel, model_id)

    def require(self, model_id: int) -> MlModel:
        model = self.get(model_id)
        if model is None:
            raise NotFoundError(f"model {model_id} not found")
        return model

    def create(self, data: ModelIn) -> MlModel:
        duplicate = self._session.scalar(
            select(MlModel.id).where(MlModel.name == data.name, MlModel.version == data.version)
        )
        if duplicate is not None:
            raise ConflictError(f"model {data.name} {data.version} already registered")
        model = MlModel(**data.model_dump())
        self._session.add(model)
        self._session.flush()
        return model

    def list(self) -> list[MlModel]:
        return list(self._session.scalars(select(MlModel).order_by(MlModel.id)))


class RiskPolicyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_active(self) -> RiskPolicy | None:
        return self._session.scalar(select(RiskPolicy).where(RiskPolicy.is_active.is_(True)))


class PredictionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        device: Device,
        model: MlModel,
        rul_cycles: Decimal,
        features: dict[str, Any] | None = None,
        telemetry_until: datetime | None = None,
    ) -> BatteryPrediction:
        policy = RiskPolicyRepository(self._session).get_active()
        classifier = RiskClassifier.from_policy(policy) if policy else RiskClassifier()
        prediction = BatteryPrediction(
            device_id=device.id,
            model_id=model.id,
            risk_policy_id=policy.id if policy else None,
            rul_cycles=rul_cycles,
            risk_level=classifier.classify(rul_cycles),
            features=features,
            telemetry_until=telemetry_until,
        )
        self._session.add(prediction)
        self._session.flush()
        return prediction

    def list_for_device(self, device: Device, limit: int = 50) -> list[BatteryPrediction]:
        stmt = (
            select(BatteryPrediction)
            .where(BatteryPrediction.device_id == device.id)
            .order_by(BatteryPrediction.predicted_at.desc(), BatteryPrediction.id.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt))

    def latest_for_device(self, device: Device) -> BatteryPrediction | None:
        rows = self.list_for_device(device, limit=1)
        return rows[0] if rows else None

    def summary(self) -> RiskSummaryOut:
        latest_ids = select(func.max(BatteryPrediction.id)).group_by(BatteryPrediction.device_id)
        stmt = (
            select(BatteryPrediction.risk_level, func.count())
            .where(BatteryPrediction.id.in_(latest_ids))
            .group_by(BatteryPrediction.risk_level)
        )
        by_risk = {level.value: 0 for level in RiskLevel}
        for level, count in self._session.execute(stmt):
            by_risk[RiskLevel(level).value] = count
        return RiskSummaryOut(
            total_devices=DeviceRepository(self._session).count(),
            devices_with_prediction=sum(by_risk.values()),
            by_risk=by_risk,
        )
