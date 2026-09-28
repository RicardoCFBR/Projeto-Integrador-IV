import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.repositories import (
    ConflictError,
    DeviceRepository,
    ModelRepository,
    NotFoundError,
    PredictionRepository,
    TelemetryRepository,
)
from app.schemas import (
    DeviceDetailOut,
    DeviceOut,
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


def _not_found(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


def _conflict(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_exception_handler(NotFoundError, _not_found)
    app.add_exception_handler(ConflictError, _conflict)
    app.include_router(router)
    return app


app = create_app()
