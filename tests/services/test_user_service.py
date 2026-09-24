from unittest.mock import (
    Mock,
    MagicMock,
    AsyncMock,
    patch
)

import pytest
from fastapi import HTTPException

from app.core.exceptions import (
    EmailAlreadyExists,
    UsernameAlreadyExists,
)
from app.core.permissions import RoleChecker
from app.models.user import User
from app.schemas.user import UserUpdate, UserCreate
from app.services.user_service import get_user_by_id, update_user, create_user, delete_user, update_user_role, get_users


@pytest.mark.asyncio
async def test_get_user_by_id_returns_user():
    user = User(
        id=10,
        username="Fedor",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hash",
        disabled=False,
        role="user",
    )

    uow = Mock()
    uow.users = Mock()

    uow.users.get_by_id = AsyncMock(return_value=user)

    result = await get_user_by_id(
        uow=uow,
        user_id=10
    )

    assert result == user

    uow.users.get_by_id.assert_awaited_once_with(10)


@pytest.mark.asyncio
async def test_get_user_by_id_returns_none():
    user = User(
        id=10,
        username="Fedor",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hash",
        disabled=False,
        role="user",
    )

    uow = Mock()
    uow.users = Mock()

    uow.users.get_by_id = AsyncMock(
        return_value=None
    )

    result = await get_user_by_id(
        uow=uow,
        user_id=999
    )

    assert result is None

    uow.users.get_by_id.assert_awaited_once_with(999)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "repository_result",
    [
        User(
            id=10,
            username="Fedor",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hash",
            disabled=False,
            role="user",
        ),
        None,
    ],
)
async def test_get_user_by_id(repository_result):
    uow = Mock()
    uow.users = Mock()

    uow.users.get_by_id = AsyncMock(return_value=repository_result)

    result = await get_user_by_id(
        uow=uow,
        user_id=10
    )

    assert result is repository_result

    uow.users.get_by_id.assert_awaited_once_with(10)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected_username, expected_email",
    [
        (
                UserUpdate(username="new_username"),
                "new_username",
                "test@example.com",
        ),
        (
                UserUpdate(email="new@example.com"),
                "test_user",
                "new@example.com",
        ),
        (
                UserUpdate(
                    username="new_username",
                    email="new@example.com",
                ),
                "new_username",
                "new@example.com",
        ),
        (
                UserUpdate(),
                "test_user",
                "test@example.com",
        ),
    ],
)
async def test_update_user(
        payload,
        expected_username,
        expected_email,
):
    user = User(
        id=10,
        username="test_user",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hash",
        disabled=False,
        role="user",
    )

    uow = Mock()
    uow.users = Mock()

    uow.users.get_by_id = AsyncMock(
        return_value=user
    )

    result = await update_user(
        uow=uow,
        user_id=10,
        user_data=payload,
    )

    assert result is user
    assert result.username == expected_username
    assert result.email == expected_email

    uow.users.get_by_id.assert_awaited_once_with(10)


@pytest.mark.asyncio
async def test_update_user_returns_none_when_user_not_found():
    uow = Mock()
    uow.users = Mock()

    uow.users.get_by_id = AsyncMock(
        return_value=None
    )

    result = await update_user(
        uow=uow,
        user_id=999,
        user_data=UserUpdate(
            username="new_username"
        ),
    )

    assert result is None

    uow.users.get_by_id.assert_awaited_once_with(999)


@pytest.mark.asyncio
async def test_create_user_raises_error_when_email_exists():
    user_data = UserCreate(
        username="Fedor",
        email="fedor@example.com",
        password="password123",
    )

    existing_user = User(
        id=1,
        username="AnotherUser",
        email="fedor@example.com",
        hashed_password="hash",
    )

    uow = Mock()
    uow.users = Mock()

    uow.users.get_by_email = AsyncMock(
        return_value=existing_user
    )

    uow.users.get_by_username = AsyncMock()

    uow.users.create = Mock()

    with pytest.raises(EmailAlreadyExists):
        await create_user(
            uow=uow,
            user_data=user_data,
        )

    uow.users.get_by_email.assert_awaited_once_with(
        "fedor@example.com"
    )

    uow.users.get_by_username.assert_not_called()

    uow.users.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_user_raises_error_when_username_exists():
    user_data = UserCreate(
        username="Fedor",
        email="fedor@example.com",
        password="password123",
    )

    existing_user = User(
        id=1,
        username="Fedor",
        email="another@example.com",
        hashed_password="hash",
    )

    uow = Mock()
    uow.users = Mock()

    uow.users.get_by_email = AsyncMock(
        return_value=None
    )

    uow.users.get_by_username = AsyncMock(
        return_value=existing_user
    )

    uow.users.create = Mock()

    with pytest.raises(UsernameAlreadyExists):
        await create_user(
            uow=uow,
            user_data=user_data,
        )

    uow.users.get_by_email.assert_awaited_once_with(
        "fedor@example.com"
    )

    uow.users.get_by_username.assert_awaited_once_with(
        "Fedor"
    )

    uow.users.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_user_successfully():
    uow = MagicMock()

    uow.users.get_by_email = AsyncMock(
        return_value=None
    )

    uow.users.get_by_username = AsyncMock(
        return_value=None
    )

    user = MagicMock()

    uow.users.create.return_value = user

    user_data = UserCreate(
        username="test_user",
        email="test@example.com",
        password="test_password"
    )

    with patch(
            "app.services.user_service.get_password_hash"
    ) as mock_hash:
        mock_hash.return_value = "test_hash"

        result = await create_user(
            uow=uow,
            user_data=user_data
        )

    assert result is user

    mock_hash.assert_called_once_with(
        "test_password"
    )

    uow.users.get_by_email.assert_awaited_once_with(
        "test@example.com"
    )

    uow.users.get_by_username.assert_awaited_once_with(
        "test_user"
    )

    uow.users.create.assert_called_once_with(
        username="test_user",
        email="test@example.com",
        hashed_password="test_hash"
    )


@pytest.mark.asyncio
async def test_create_user_email_already_exists():
    uow = MagicMock()

    existing_user = MagicMock()

    uow.users.get_by_email = AsyncMock(
        return_value=existing_user
    )

    uow.users.get_by_username = AsyncMock()

    uow.users.create = MagicMock()

    user_data = UserCreate(
        username="test_user",
        email="test@example.com",
        password="test_password"
    )

    with patch(
            "app.services.user_service.get_password_hash"
    ) as mock_hash:
        with pytest.raises(EmailAlreadyExists):
            await create_user(
                uow=uow,
                user_data=user_data
            )

    uow.users.get_by_email.assert_awaited_once_with(
        "test@example.com"
    )

    uow.users.get_by_username.assert_not_awaited()

    uow.users.create.assert_not_called()

    mock_hash.assert_not_called()


@pytest.mark.asyncio
async def test_create_user_username_already_exists():
    uow = MagicMock()

    existing_user = MagicMock()

    uow.users.get_by_email = AsyncMock(
        return_value=None
    )

    uow.users.get_by_username = AsyncMock(
        return_value=existing_user
    )

    uow.users.create = MagicMock()

    user_data = UserCreate(
        username="test_user",
        email="test@example.com",
        password="test_password"
    )

    with patch(
            "app.services.user_service.get_password_hash"
    ) as mock_hash:
        with pytest.raises(UsernameAlreadyExists):
            await create_user(
                uow=uow,
                user_data=user_data
            )

    uow.users.get_by_email.assert_awaited_once_with(
        "test@example.com"
    )

    uow.users.get_by_username.assert_awaited_once_with(
        "test_user"
    )

    mock_hash.assert_not_called()

    uow.users.create.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected_username, expected_email",
    [
        (
                {
                    "username": "new_username"
                },
                "new_username",
                "test@example.com"
        ),
        (
                {
                    "email": "new@example.com"
                },
                "test_user",
                "new@example.com"
        ),
        (
                {
                    "username": "new_username",
                    "email": "new@example.com"
                },
                "new_username",
                "new@example.com"
        ),
        (
                {},
                "test_user",
                "test@example.com"
        )
    ]
)
async def test_update_user(
        payload,
        expected_username,
        expected_email
):
    uow = MagicMock()

    user = MagicMock()

    user.id = 10
    user.username = "test_user"
    user.email = "test@example.com"

    uow.users.get_by_id = AsyncMock(
        return_value=user
    )

    user_data = UserUpdate(
        **payload
    )

    result = await update_user(
        uow=uow,
        user_id=10,
        user_data=user_data
    )

    assert result is user

    assert user.username == expected_username
    assert user.email == expected_email

    uow.users.get_by_id.assert_awaited_once_with(
        10
    )


@pytest.mark.asyncio
async def test_update_user_not_found():
    uow = MagicMock()

    uow.users.get_by_id = AsyncMock(
        return_value=None
    )

    user_data = UserUpdate(
        username="new_username"
    )

    result = await update_user(
        uow=uow,
        user_id=999,
        user_data=user_data
    )

    assert result is None

    uow.users.get_by_id.assert_awaited_once_with(
        999
    )


@pytest.mark.asyncio
async def test_delete_user_success():
    uow = MagicMock()

    user = MagicMock()

    uow.users.get_by_id = AsyncMock(
        return_value=user
    )

    uow.users.delete = AsyncMock()

    result = await delete_user(
        uow=uow,
        user_id=10
    )

    assert result is True

    uow.users.get_by_id.assert_awaited_once_with(10)

    uow.users.delete.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_delete_user_not_found():
    uow = MagicMock()

    uow.users.get_by_id = AsyncMock(
        return_value=None
    )

    uow.users.delete = AsyncMock()

    result = await delete_user(
        uow=uow,
        user_id=999
    )

    assert result is None

    uow.users.get_by_id.assert_awaited_once_with(999)

    uow.users.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_user_role_success():
    uow = MagicMock()

    user = MagicMock()

    user.id = 10
    user.username = "test_user"
    user.email = "test@example.com"
    user.role = "user"

    uow.users.get_by_id = AsyncMock(
        return_value=user
    )

    result = await update_user_role(
        uow=uow,
        user_id=10,
        role="admin"
    )

    assert result is user
    assert user.role == "admin"

    uow.users.get_by_id.assert_awaited_once_with(10)


@pytest.mark.asyncio
async def test_update_user_role_not_found():
    uow = MagicMock()

    uow.users.get_by_id = AsyncMock(
        return_value=None
    )

    result = await update_user_role(
        uow=uow,
        user_id=999,
        role="admin"
    )

    assert result is None

    uow.users.get_by_id.assert_awaited_once_with(999)


@pytest.mark.asyncio
async def test_get_users():
    uow = MagicMock()

    users = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]

    uow.users.get_all = AsyncMock(
        return_value=users
    )

    result = await get_users(
        uow=uow
    )

    assert result is users

    uow.users.get_all.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_role_checker_allowed_role():
    checker = RoleChecker(["admin"])

    current_user = MagicMock()
    current_user.role = "admin"

    result = await checker(
        current_user=current_user
    )

    assert result is current_user


@pytest.mark.asyncio
async def test_role_checker_forbidden_role():
    checker = RoleChecker(["admin"])

    current_user = MagicMock()
    current_user.role = "user"

    with pytest.raises(HTTPException) as exc_info:
        await checker(
            current_user=current_user
        )

    assert exc_info.value.status_code == 403
