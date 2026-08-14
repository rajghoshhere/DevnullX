"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str
    vehicle_verification_provider: str = "fake"
    api_setu_base_url: str = ""
    api_setu_api_key: str = ""
    api_setu_client_id: str = ""
    api_setu_timeout_seconds: float = 10.0
    api_setu_max_attempts: int = 3
    api_setu_backoff_seconds: float = 0.2


@lru_cache
def get_settings() -> Settings:
    return Settings()
