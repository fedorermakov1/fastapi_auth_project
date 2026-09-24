
from app.cache.cache import Cache
from app.rate_limit.limiter import RateLimiter

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.core.config import settings
from app.models import User
from app.repositories.dependencies import get_uow
from app.repositories.unit_of_work import UnitOfWork

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token"
)


def get_cache(request: Request) -> Cache:
    return request.app.state.cache


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        uow: UnitOfWork = Depends(get_uow)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (JWTError, ValueError):
        raise credentials_exception

    user = await uow.users.get_by_id(user_id)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(
            status_code=400,
            detail="Inactive user"
        )

    return current_user
