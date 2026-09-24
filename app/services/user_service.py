from app.core.security import get_password_hash
from app.core.exceptions import (
    EmailAlreadyExists,
    UsernameAlreadyExists
)
from app.core.roles import RoleEnum
from app.repositories.unit_of_work import UnitOfWork
from app.schemas.user import UserCreate, UserUpdate
from app.models import User


async def create_user(
        uow: UnitOfWork,
        user_data: UserCreate
):
    existing_email = await uow.users.get_by_email(
        user_data.email
    )

    if existing_email:
        raise EmailAlreadyExists(
            user_data.email
        )

    existing_username = await uow.users.get_by_username(
        user_data.username
    )

    if existing_username:
        raise UsernameAlreadyExists(
            user_data.username
        )

    hashed_password = get_password_hash(
        user_data.password
    )

    user = uow.users.create(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )

    return user


async def register_user_with_task(
        uow: UnitOfWork,
        user_data: UserCreate
):
    existing_email = await uow.users.get_by_email(
        user_data.email
    )

    if existing_email:
        raise EmailAlreadyExists(
            user_data.email
        )

    existing_username = await uow.users.get_by_username(
        user_data.username
    )

    if existing_username:
        raise UsernameAlreadyExists(
            user_data.username
        )

    hashed_password = get_password_hash(
        user_data.password
    )

    user = uow.users.create(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )

    await uow.flush()

    uow.tasks.create(
        title="Complete profile",
        description="Complete your profile",
        user_id=user.id
    )

    return user


async def get_users(
        uow: UnitOfWork
):
    return await uow.users.get_all()


async def get_user_by_id(
        uow: UnitOfWork,
        user_id: int
) -> User | None:
    return await uow.users.get_by_id(
        user_id
    )


async def update_user(
        uow: UnitOfWork,
        user_id: int,
        user_data: UserUpdate
):
    user = await uow.users.get_by_id(
        user_id
    )

    if user is None:
        return None

    if user_data.username is not None:
        user.username = user_data.username

    if user_data.email is not None:
        user.email = user_data.email

    return user


async def delete_user(
        uow: UnitOfWork,
        user_id: int
):
    user = await uow.users.get_by_id(
        user_id
    )

    if user is None:
        return None

    await uow.users.delete(user)

    return True


async def update_user_role(
        uow: UnitOfWork,
        user_id: int,
        role: RoleEnum
):
    user = await uow.users.get_by_id(
        user_id
    )

    if user is None:
        return None

    user.role = role

    return user