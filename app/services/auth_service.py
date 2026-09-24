from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token
)

from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.repositories.unit_of_work import UnitOfWork
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthTokens

from uuid import UUID

def _create_refresh_session(
        uow: UnitOfWork,
        user_id: int
):
    refresh_token = create_refresh_token()

    token_id, secret = refresh_token.split(".", 1)

    token_id = UUID(token_id)

    expires_at = (
            datetime.now(timezone.utc)
            + timedelta(days=7)
    )

    uow.refresh_tokens.create(
        user_id=user_id,
        token_id=token_id,
        secret=secret,
        expires_at=expires_at
    )

    return refresh_token




async def authenticate_user(
        user_repository: UserRepository,
        username: str,
        password: str
):
    user = await user_repository.get_by_username(
        username
    )

    if user is None:
        return None

    if not verify_password(
            password,
            user.hashed_password
    ):
        return None

    return user


async def login(
        uow: UnitOfWork,
        username: str,
        password: str
):
    user = await authenticate_user(
        user_repository=uow.users,
        username=username,
        password=password
    )

    if user is None:
        return None

    access_token = create_access_token(
        data={
            "sub": str(user.id)
        },
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    refresh_token = _create_refresh_session(
        uow=uow,
        user_id=user.id
    )

    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token
    )


async def refresh_access_token(
        uow: UnitOfWork,
        refresh_token: str
):
    refresh_token_record = await (
        uow.refresh_tokens.get_by_token(
            refresh_token
        )
    )

    if refresh_token_record is None:
        return None

    user = refresh_token_record.user

    uow.refresh_tokens.revoke(
        refresh_token_record
    )

    new_refresh_token = _create_refresh_session(
        uow=uow,
        user_id=user.id
    )

    access_token = create_access_token(
        data={
            "sub": str(user.id)
        },
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    return AuthTokens(
        access_token=access_token,
        refresh_token=new_refresh_token
    )


async def logout(
    uow: UnitOfWork,
    refresh_token: str
):
    refresh_token_record = await (
        uow.refresh_tokens.get_by_token(
            refresh_token
        )
    )

    if refresh_token_record:
        uow.refresh_tokens.revoke(
            refresh_token_record
        )



