import asyncio

import pytest

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core import settings
from app.models import User
from app.repositories.unit_of_work import UnitOfWork


def test_commit_then_rollback():
    async def run_test():
        engine = create_async_engine(
            settings.TEST_DATABASE_URL,
            echo=True,
            poolclass=NullPool,
        )

        connection = await engine.connect()

        transaction = await connection.begin()

        session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as db:
            await db.execute(
                text(
                    """
                    INSERT INTO users
                    (username, email, full_name, hashed_password, disabled, role)
                    VALUES
                    (
                        'transaction_test',
                        'transaction@test.com',
                        'Test',
                        'fake_hash',
                        false,
                        'user'
                    )
                    """
                )
            )

            await db.commit()

        await transaction.rollback()

        await connection.close()
        await engine.dispose()

    asyncio.run(run_test())


def test_transaction_fixtures(test_connection, test_transaction):
    print("\nCONNECTION:", test_connection)
    print("TRANSACTION:", test_transaction)


import pytest


@pytest.mark.anyio
async def test_real_app_commit(
        async_client,
        test_connection,
        test_transaction,
):
    response = await async_client.post(
        "/test-transaction"
    )

    assert response.status_code == 200

    print(response.json())


@pytest.mark.asyncio
async def test_commit_inside_outer_transaction(
        test_connection,
        test_transaction,
        test_session_factory,
):
    async with test_session_factory() as db:
        user = User(
            username="commit_test",
            email="commit@test.com",
            full_name="Commit Test",
            hashed_password="fake_hash",
            disabled=False,
            role="user",
        )

        db.add(user)

        await db.commit()

    await test_transaction.rollback()

    async with test_session_factory() as db:
        result = await db.execute(
            select(User).where(
                User.username == "commit_test"
            )
        )

        user = result.scalar_one_or_none()

        assert user is None


@pytest.mark.asyncio
async def test_real_app_commit(
        async_client,
        test_connection,
        test_transaction,
):
    response = await async_client.post(
        "/test-transaction"
    )

    assert response.status_code == 200

    print(response.json())

    await test_transaction.rollback()

    result = await test_connection.execute(
        select(User).where(
            User.username == "commit_test"
        )
    )

    user = result.scalar_one_or_none()

    assert user is None


@pytest.mark.asyncio
async def test_real_app_rollback(
        async_client,
        verification_session,
):
    response = await async_client.post(
        "/test-transaction-rollback"
    )

    assert response.status_code == 200

    result = await verification_session.execute(
        select(User).where(
            User.username == "rollback_test"
        )
    )

    user = result.scalar_one_or_none()

    assert user is None


@pytest.mark.asyncio
async def test_transaction_error(
        async_client,
        verification_session
):
    response = await async_client.post(
        "/test-transaction-error"
    )

    assert response.status_code == 500

    result = await verification_session.execute(
        select(User).where(
            User.username == "atomic_test"
        )
    )

    user = result.scalar_one_or_none()

    assert user is None


@pytest.mark.asyncio
async def test_transaction_context_commit(
        async_client,
        verification_session,
):
    response = await async_client.post(
        "/test-transaction-context"
    )

    assert response.status_code == 200

    result = await verification_session.execute(
        select(User).where(
            User.username == "context_test"
        )
    )

    user = result.scalar_one_or_none()

    assert user is not None


@pytest.mark.asyncio
async def test_transaction_context_error(
        async_client,
        verification_session,
):
    response = await async_client.post(
        "/test-transaction-context-error"
    )

    assert response.status_code == 500

    result = await verification_session.execute(
        select(User).where(
            User.username == "context_error_test"
        )
    )

    user = result.scalar_one_or_none()

    assert user is None


@pytest.mark.asyncio
async def test_commit_inside_begin(
        async_client,
        verification_session,
):
    response = await async_client.post(
        "/test-commit-inside-begin"
    )

    assert response.status_code == 200

    result = await verification_session.execute(
        select(User).where(
            User.username == "commit_inside_begin"
        )
    )

    user = result.scalar_one_or_none()

    assert user is not None


@pytest.mark.asyncio
async def test_uow_commit(
        test_session_factory,
        verification_session,
):
    async with test_session_factory() as db:
        async with UnitOfWork(db) as uow:
            user = uow.users.create(
                username="uow_commit_test",
                email="uow_commit@test.com",
                hashed_password="fake_hash",
            )

    result = await verification_session.execute(
        select(User).where(
            User.username == "uow_commit_test"
        )
    )

    user = result.scalar_one_or_none()

    assert user is not None


@pytest.mark.asyncio
async def test_uow_rollback_on_exception(
        test_session_factory,
        verification_session,
):
    with pytest.raises(ValueError):
        async with test_session_factory() as db:
            async with UnitOfWork(db) as uow:
                uow.users.create(
                    username="uow_rollback_test",
                    email="uow_rollback@test.com",
                    hashed_password="fake_hash",
                )

                raise ValueError("Something went wrong")

    result = await verification_session.execute(
        select(User).where(
            User.username == "uow_rollback_test"
        )
    )

    user = result.scalar_one_or_none()

    assert user is None


@pytest.mark.parametrize(
    "username,email,hashed_password",
    [
        ("user1", "user1@test.com", "hash1"),
        ("user2", "user2@test.com", "hash2"),
        ("admin", "admin@test.com", "hash3"),
    ],
    ids=[
        "regular_user_1",
        "regular_user_2",
        "admin_user",
    ]
)
@pytest.mark.asyncio
async def test_uow_create_user(
    uow,
    verification_session,
    username,
    email,
    hashed_password,
):
    async with uow:
        user = uow.users.create(
            username=username,
            email=email,
            hashed_password=hashed_password,
        )

    result = await verification_session.execute(
        select(User).where(
            User.username == username
        )
    )

    saved_user = result.scalar_one_or_none()

    assert saved_user is not None
    assert saved_user.username == username
    assert saved_user.email == email
    assert saved_user.hashed_password == hashed_password

@pytest.mark.asyncio
async def test_uow_rollback_on_error(
    uow,
    verification_session,
):
    with pytest.raises(ValueError):
        async with uow:
            uow.users.create(
                username="uow_rollback",
                email="uow_rollback@test.com",
                hashed_password="hash",
            )

            raise ValueError("something went wrong")

    result = await verification_session.execute(
        select(User).where(
            User.username == "uow_rollback"
        )
    )

    user = result.scalar_one_or_none()

    assert user is None

@pytest.mark.asyncio
async def test_nested_commit_experiment(
    test_transaction,
    test_session_factory,
):
    async with test_session_factory() as db:

        async with db.begin_nested():
            user = User(
                username="nested_commit_test",
                email="nested_commit@test.com",
                full_name="Nested Commit Test",
                hashed_password="hash",
                disabled=False,
                role="user",
            )

            db.add(user)

            await db.flush()

            print("USER CREATED:", user.id)

            await db.commit()

            print("COMMIT INSIDE NESTED")

@pytest.mark.parametrize(
    "payload, expected_username, expected_email",
    [
        (
            {"username": "new_name"},
            "new_name",
            "test@example.com",
        ),
        (
            {"email": "new@example.com"},
            "test_user",
            "new@example.com",
        ),
        (
            {
                "username": "new_name",
                "email": "new@example.com",
            },
            "new_name",
            "new@example.com",
        ),
        (
            {},
            "test_user",
            "test@example.com",
        ),
    ],
    ids=[
        "update_username",
        "update_email",
        "update_username_and_email",
        "update_nothing",
    ],
)
@pytest.mark.asyncio
async def test_update_user(
    async_client,
    test_user,
    verification_session,
    payload,
    expected_username,
    expected_email,
):
    response = await async_client.put(
        f"/users/{test_user.id}",
        json=payload
    )

    assert response.status_code == 200

    result = await verification_session.execute(
        select(User).where(
            User.id == test_user.id
        )
    )

    updated_user = result.scalar_one_or_none()

    assert updated_user.username == expected_username
    assert updated_user.email == expected_email


@pytest.mark.asyncio
async def test_create_user_integration(
    async_client,
    verification_session,
    clean_database,
):
    payload = {
        "username": "integration_user",
        "email": "integration@example.com",
        "password": "test_password",
    }

    response = await async_client.post(
        "/users/",
        json=payload,
    )

    assert response.status_code == 200

    result = await verification_session.execute(
        select(User).where(
            User.username == "integration_user"
        )
    )

    user = result.scalar_one_or_none()

    assert user is not None
    assert user.username == "integration_user"
    assert user.email == "integration@example.com"

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected_username, expected_email",
    [
        (
            {
                "username": "updated_user",
                "email": "updated@example.com",
            },
            "updated_user",
            "updated@example.com",
        ),
        (
            {
                "username": "new_username",
            },
            "new_username",
            "integration@example.com",
        ),
        (
            {
                "email": "new_email@example.com",
            },
            "integration_user",
            "new_email@example.com",
        ),
    ],
)
async def test_update_user_integration(
    async_client,
    verification_session,
    clean_database,
    payload,
    expected_username,
    expected_email,
):
    user = User(
        username="integration_user",
        email="integration@example.com",
        hashed_password="test_hash",
        disabled=False,
        role="user",
    )

    verification_session.add(user)
    await verification_session.commit()
    await verification_session.refresh(user)

    user_id = user.id

    response = await async_client.put(
        f"/users/{user_id}",
        json=payload,
    )

    assert response.status_code == 200

    await verification_session.rollback()

    result = await verification_session.execute(
        select(User).where(
            User.id == user_id
        )
    )

    updated_user = result.scalar_one_or_none()

    assert updated_user is not None
    assert updated_user.username == expected_username
    assert updated_user.email == expected_email


@pytest.mark.asyncio
async def test_update_user_role_integration(
    async_client,
    verification_session,
    admin_auth_token,
    clean_database,
):
    user = User(
        username="role_user",
        email="role@example.com",
        hashed_password="test_hash",
        disabled=False,
        role="user",
    )

    verification_session.add(user)
    await verification_session.commit()
    await verification_session.refresh(user)

    user_id = user.id

    response = await async_client.patch(
        f"/users/{user_id}/role",
        json={"role": "admin"},
        headers={
            "Authorization": f"Bearer {admin_auth_token}",
        },
    )

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_update_user_role_not_found_integration(
    async_client,
    verification_session,
    clean_database,
):
    response = await async_client.patch(
        "/users/999999/role",
        json={"role": "admin"},
    )

    assert response.status_code == 404