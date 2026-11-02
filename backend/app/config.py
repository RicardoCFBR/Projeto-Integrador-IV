from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

RUL_MODEL_DIR = Path(__file__).resolve().parents[2] / "ml" / "artifacts" / "v2_2_tuned"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "BatteryCare API"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/fleet_battery"
    ingest_batch_max: int = 5000
    read_only_demo: bool = False
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    rul_model_path: Path = RUL_MODEL_DIR / "battery_rul_random_forest_v2_2_tuned.joblib"
    rul_metadata_path: Path = RUL_MODEL_DIR / "battery_rul_random_forest_v2_2_tuned_metadata.json"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        """Render provides a standard postgresql:// URL; use the installed psycopg driver."""
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
