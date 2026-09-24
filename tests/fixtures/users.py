import pytest_asyncio

from app.models.user import User
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def test_user(test_session_factory):
    async with test_session_factory() as db:
        user = User(
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("test_password"),
            disabled=False,
            role="user",
        )

        db.add(user)

        await db.commit()
        await db.refresh(user)

        user_id = user.id

    yield user

    async with test_session_factory() as db:
        user = await db.get(User, user_id)

        if user is not None:
            await db.delete(user)
            await db.commit()

@pytest_asyncio.fixture
async def admin_user(test_session_factory):
    async with test_session_factory() as db:
        user = User(
            username="admin_user",
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=get_password_hash("admin_password"),
            disabled=False,
            role="admin",
        )

        db.add(user)

        await db.commit()
        await db.refresh(user)

        user_id = user.id

    yield user

    async with test_session_factory() as db:
        user = await db.get(User, user_id)

        if user is not None:
            await db.delete(user)
            await db.commit()