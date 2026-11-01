import logging
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.features import InsufficientHistoryError, build_features
from app.inference import ModelUnavailableError, RulPredictor, get_predictor
from app.repositories import (
    ConflictError,
    DeviceRepository,
    ModelRepository,
    NotFoundError,
    PredictionRepository,
    TelemetryRepository,
)
from app.risk import RiskLevel
from app.schemas import (
    AlertOut,
    DeviceDetailOut,
    DeviceOut,
    DeviceOverviewOut,
    FleetTrendPointOut,
    HealthOut,
    IngestResult,
    ModelIn,
    ModelOut,
    PredictionIn,
    PredictionOut,
    RiskSummaryOut,
    TelemetryBatchIn,
    TelemetryOut,
)

logger = logging.getLogger(__name__)

SessionDep = Annotated[Session, Depends(get_session)]
PredictorDep = Annotated[RulPredictor, Depends(get_predictor)]
router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok")


@router.post("/telemetry", status_code=status.HTTP_201_CREATED, response_model=IngestResult)
def ingest_telemetry(batch: TelemetryBatchIn, db: SessionDep) -> IngestResult:
    result = TelemetryRepository(db).bulk_insert(batch.readings)
    db.commit()
    logger.info("telemetry batch ingested inserted=%s skipped=%s", result.inserted, result.skipped)
    return result


@router.get("/devices", response_model=list[DeviceOut])
def list_devices(db: SessionDep) -> list[DeviceOut]:
    return [DeviceOut.model_validate(device) for device in DeviceRepository(db).list()]


@router.get("/devices/overview", response_model=list[DeviceOverviewOut])
def devices_overview(db: SessionDep) -> list[DeviceOverviewOut]:
    readings = TelemetryRepository(db).latest_by_device()
    predictions = PredictionRepository(db).latest_by_device()
    rows = []
    for device in DeviceRepository(db).list():
        last_reading = readings.get(device.id)
        latest = predictions.get(device.id)
        rows.append(
            DeviceOverviewOut(
                **DeviceOut.model_validate(device).model_dump(),
                latest_prediction=PredictionOut.model_validate(latest) if latest else None,
                last_telemetry_at=last_reading.recorded_at if last_reading else None,
                estimated_capacity_pct=last_reading.estimated_capacity_pct
                if last_reading
                else None,
                cycle_count=last_reading.cycle_count if last_reading else None,
            )
        )
    return rows


@router.get("/devices/{code}", response_model=DeviceDetailOut)
def device_detail(code: str, db: SessionDep) -> DeviceDetailOut:
    device = DeviceRepository(db).require(code)
    latest = PredictionRepository(db).latest_for_device(device)
    return DeviceDetailOut(
        **DeviceOut.model_validate(device).model_dump(),
        latest_prediction=PredictionOut.model_validate(latest) if latest else None,
    )


@router.get("/devices/{code}/telemetry", response_model=list[TelemetryOut])
def list_telemetry(
    code: str,
    db: SessionDep,
    since: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 100,
) -> list[TelemetryOut]:
    device = DeviceRepository(db).require(code)
    rows = TelemetryRepository(db).list_for_device(device, since=since, limit=limit)
    return [TelemetryOut.model_validate(row) for row in rows]


@router.post("/models", status_code=status.HTTP_201_CREATED, response_model=ModelOut)
def register_model(data: ModelIn, db: SessionDep) -> ModelOut:
    model = ModelRepository(db).create(data)
    db.commit()
    return ModelOut.model_validate(model)


@router.get("/models", response_model=list[ModelOut])
def list_models(db: SessionDep) -> list[ModelOut]:
    return [ModelOut.model_validate(model) for model in ModelRepository(db).list()]


@router.post("/predictions", status_code=status.HTTP_201_CREATED, response_model=PredictionOut)
def register_prediction(data: PredictionIn, db: SessionDep) -> PredictionOut:
    device = DeviceRepository(db).require(data.device_code)
    model = ModelRepository(db).require(data.model_id)
    prediction = PredictionRepository(db).create(
        device=device,
        model=model,
        rul_cycles=data.rul_cycles,
        features=data.features,
        telemetry_until=data.telemetry_until,
    )
    db.commit()
    return PredictionOut.model_validate(prediction)


@router.post(
    "/devices/{code}/predictions/run",
    status_code=status.HTTP_201_CREATED,
    response_model=PredictionOut,
)
def run_prediction(
    code: str,
    db: SessionDep,
    predictor: PredictorDep,
    as_of: Annotated[datetime | None, Query()] = None,
) -> PredictionOut:
    device = DeviceRepository(db).require(code)
    snapshot = build_features(TelemetryRepository(db).history_for_device(device, until=as_of))
    model = ModelRepository(db).get_or_create(predictor.registration)
    prediction = PredictionRepository(db).create(
        device=device,
        model=model,
        rul_cycles=Decimal(str(round(predictor.predict(snapshot.values), 2))),
        features=snapshot.values,
        telemetry_until=snapshot.telemetry_until,
    )
    db.commit()
    logger.info("prediction stored device=%s rul=%s", code, prediction.rul_cycles)
    return PredictionOut.model_validate(prediction)


@router.get("/devices/{code}/predictions", response_model=list[PredictionOut])
def list_predictions(
    code: str,
    db: SessionDep,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> list[PredictionOut]:
    device = DeviceRepository(db).require(code)
    rows = PredictionRepository(db).list_for_device(device, limit=limit)
    return [PredictionOut.model_validate(row) for row in rows]


@router.get("/predictions/summary", response_model=RiskSummaryOut)
def risk_summary(db: SessionDep) -> RiskSummaryOut:
    return PredictionRepository(db).summary()


@router.get("/fleet/trend", response_model=list[FleetTrendPointOut])
def fleet_trend(
    db: SessionDep,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> list[FleetTrendPointOut]:
    trend = TelemetryRepository(db).fleet_capacity_trend(days)
    return [FleetTrendPointOut(day=day, soh_percent=average) for day, average in trend]


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(db: SessionDep) -> list[AlertOut]:
    at_risk = sorted(
        (
            prediction
            for prediction in PredictionRepository(db).latest_by_device().values()
            if prediction.risk_level != RiskLevel.LOW
        ),
        key=lambda prediction: prediction.rul_cycles,
    )
    return [
        AlertOut(
            device_code=prediction.device_code,
            risk_level=prediction.risk_level,
            rul_cycles=prediction.rul_cycles,
            predicted_at=prediction.predicted_at,
            telemetry_until=prediction.telemetry_until,
            policy_name=prediction.risk_policy.name if prediction.risk_policy else None,
            policy_source=prediction.risk_policy.source if prediction.risk_policy else None,
            high_below_cycles=prediction.risk_policy.high_below_cycles
            if prediction.risk_policy
            else None,
            medium_below_cycles=prediction.risk_policy.medium_below_cycles
            if prediction.risk_policy
            else None,
        )
        for prediction in at_risk
    ]


def _not_found(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


def _conflict(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


def _insufficient_history(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(exc)}
    )


def _model_unavailable(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": str(exc)}
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(NotFoundError, _not_found)
    app.add_exception_handler(ConflictError, _conflict)
    app.add_exception_handler(InsufficientHistoryError, _insufficient_history)
    app.add_exception_handler(ModelUnavailableError, _model_unavailable)
    app.include_router(router)
    return app


app = create_app()
