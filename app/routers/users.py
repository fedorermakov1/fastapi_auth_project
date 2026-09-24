from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_active_user
from app.core.permissions import (
    admin_required,
    check_user_access
)

from app.models.user import User

from app.schemas.user import (
    UserCreate,
    UserRead,
    UserUpdate,
    UserRoleUpdate
)

from app.repositories.unit_of_work import UnitOfWork
from app.repositories.dependencies import get_uow

from app.services.user_service import (
    create_user,
    get_user_by_id,
    get_users as get_users_service,
    update_user,
    delete_user,
    update_user_role, register_user_with_task
)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/", response_model=UserRead)
async def register_user(
        user_data: UserCreate,
        uow: UnitOfWork = Depends(get_uow, scope="function")
):
    result = await create_user(
        uow=uow,
        user_data=user_data
    )

    return result


@router.get(
    "/",
    response_model=list[UserRead],
    dependencies=[Depends(admin_required)],
)
async def get_users(
        uow: UnitOfWork = Depends(get_uow, scope="function")
):
    users = await get_users_service(
        uow=uow
    )

    return users

@router.post("/test-transaction")
async def test_transaction(
    user_data: UserCreate,
    uow: UnitOfWork = Depends(
        get_uow,
        scope="function"
    )
):
    return await register_user_with_task(
        uow=uow,
        user_data=user_data
    )


@router.get("/me", response_model=UserRead)
def read_current_user(
        current_user: User = Depends(get_current_active_user)
):
    return current_user


@router.get(
    "/admin",
    dependencies=[Depends(admin_required)],

)
async def admin_panel(
):
    return {
        "message": "Welcome, Admin!"
    }


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    dependencies=[Depends(admin_required)],
)
async def change_user_role(
        user_id: int,
        role_data: UserRoleUpdate,
        uow: UnitOfWork = Depends(get_uow, scope="function")
):
    user = await update_user_role(
        uow=uow,
        user_id=user_id,
        role=role_data.role
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
        user_id: int,
        _: User = Depends(check_user_access),
        uow: UnitOfWork = Depends(get_uow, scope="function")
):
    user = await get_user_by_id(
        uow=uow,
        user_id=user_id
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user_by_id(
        user_id: int,
        user_data: UserUpdate,
        uow: UnitOfWork = Depends(get_uow, scope="function")
):
    user = await update_user(
        uow=uow,
        user_id=user_id,
        user_data=user_data
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.delete("/{user_id}")
async def delete_user_by_id(
        user_id: int,
        uow: UnitOfWork = Depends(get_uow, scope="function")
):
    deleted = await delete_user(
        uow=uow,
        user_id=user_id
    )

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    return {
        "message": "User deleted successfully"
    }
