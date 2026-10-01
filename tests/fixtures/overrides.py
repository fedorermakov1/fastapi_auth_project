import pytest

from app.main import app

from app.core.dependencies import get_cache
from app.repositories.dependencies import get_uow

from tests.fakes.cache import FakeCache
from tests.fakes.uow import FakeUnitOfWork

def fake_get_cache():
    return FakeCache()


def fake_get_uow():
    return FakeUnitOfWork()

@pytest.fixture
def fake_cache():
    app.dependency_overrides[get_cache] = fake_get_cache

    yield

    app.dependency_overrides.pop(
        get_cache,
        None,
    )


@pytest.fixture
def fake_uow():
    app.dependency_overrides[get_uow] = fake_get_uow

    yield

    app.dependency_overrides.pop(
        get_uow,
        None,
    )
