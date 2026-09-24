from fastapi import Depends, HTTPException

from app.core.dependencies import get_current_active_user
from app.models import User

class RoleChecker:

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(
            self,
            current_user: User = Depends(get_current_active_user)
    ):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions"
            )

        return current_user

admin_required = RoleChecker(
    ["admin"]
)


moderator_required = RoleChecker(
    ["admin", "moderator"]
)

async def check_user_access(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role == "admin":
        return current_user

    if current_user.id == user_id:
        return current_user

    raise HTTPException(
        status_code=403,
        detail="Not enough permissions"
    )