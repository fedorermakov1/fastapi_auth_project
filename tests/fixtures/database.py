import pytest_asyncio

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.database.session import get_db
from app.main import app

from sqlalchemy import text

from app.repositories.unit_of_work import UnitOfWork



@pytest_asyncio.fixture
async def test_connection():
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=True,
        poolclass=NullPool,
    )

    connection = await engine.connect()

    yield connection

    await connection.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def test_transaction(test_connection):
    transaction = await test_connection.begin()

    yield transaction

    if transaction.is_active:
        await transaction.rollback()


@pytest_asyncio.fixture
async def test_session_factory(test_connection):
    return async_sessionmaker(
        bind=test_connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def test_db_override(test_session_factory):
    async def override_get_db():
        async with test_session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.pop(
        get_db,
        None,
    )


@pytest_asyncio.fixture
async def verification_session():
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=True,
        poolclass=NullPool,
    )

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as db:
        yield db

    await engine.dispose()


@pytest_asyncio.fixture
async def clean_database():
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=True,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                TRUNCATE TABLE
                    refresh_tokens,
                    tasks,
                    users
                RESTART IDENTITY CASCADE
                """
            )
        )

    await engine.dispose()

@pytest_asyncio.fixture
async def uow(test_session_factory):
    async with test_session_factory() as db:
        yield UnitOfWork(db)