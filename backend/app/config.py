from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Fleet Battery Health API"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/fleet_battery"
    ingest_batch_max: int = 5000


@lru_cache
def get_settings() -> Settings:
    return Settings()
