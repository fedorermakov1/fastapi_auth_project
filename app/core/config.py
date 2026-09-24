from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str

    TEST_DATABASE_URL: str | None = None

    ALEMBIC_DATABASE_URL: str | None = None

    ALEMBIC_TEST_DATABASE_URL: str | None = None

    RABBITMQ_URL: str

    MAX_RETRIES: int

    RATE_LIMIT_STRATEGY: str = "fixed"

    SECRET_KEY: str

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore"
    )


settings = Settings()
