from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database_config import database_settings

engine = create_async_engine(
    database_settings.DATABASE_URL,
    echo=True
)



