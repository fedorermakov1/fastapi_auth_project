from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database_config import database_settings


def create_celery_session_factory():
    engine = create_engine(
        database_settings.DATABASE_URL.replace(
            "postgresql+asyncpg://",
            "postgresql+psycopg2://",
        ),
    )

    return sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )