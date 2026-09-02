from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://fp_app:change_me@localhost:5432/financial_platform"
    mlflow_tracking_uri: str = "http://localhost:5000"
    stooq_api_key: str | None = None
    gus_client_id: str | None = None
    data_start_year: int = 2018
    yahoo_enable: bool = True
    model_artifact_dir: str = "artifacts/models"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
