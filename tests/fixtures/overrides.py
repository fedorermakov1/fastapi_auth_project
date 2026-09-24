import pytest

from app.main import app

from app.core.dependencies import get_cache
from app.repositories.dependencies import get_uow
from app.core.security import get_current_active_user

from tests.fakes.cache import FakeCache
from tests.fakes.uow import FakeUnitOfWork
from app.models.user import User


def fake_get_cache():
    return FakeCache()


def fake_get_uow():
    return FakeUnitOfWork()


def fake_get_current_active_user():
    return User(
        id=1,
        username="test_user",
        email="test@example.com",
        full_name="Test User",
        hashed_password="fake_hash",
        disabled=False,
        role="user",
    )


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


@pytest.fixture
def fake_current_user():
    app.dependency_overrides[
        get_current_active_user
    ] = fake_get_current_active_user

    yield

    app.dependency_overrides.pop(
        get_current_active_user,
        None,
    )