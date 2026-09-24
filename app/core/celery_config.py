from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class CelerySettings(BaseSettings):
    RABBITMQ_URL: str
    REDIS_URL: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore"
    )



celery_settings = CelerySettings()