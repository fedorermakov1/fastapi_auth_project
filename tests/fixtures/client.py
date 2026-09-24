import pytest
import pytest_asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_client(test_db_override):
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client(test_db_override):
    transport = ASGITransport(
        app=app,
        raise_app_exceptions=False,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client