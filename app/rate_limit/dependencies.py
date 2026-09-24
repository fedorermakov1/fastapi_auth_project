from fastapi import Depends, HTTPException, Request

from app.core.dependencies import get_rate_limiter
from app.core.dependencies import get_current_active_user
from app.models import User
from app.rate_limit.identity import get_user_client_id, get_ip_client_id
from app.rate_limit.limiter import RateLimiter


def user_rate_limit(
    limit: int,
    window: int
):
    async def dependency(
        request: Request,
        current_user: User = Depends(
            get_current_active_user
        ),
        rate_limiter: RateLimiter = Depends(
            get_rate_limiter
        )
    ):
        client_id = get_user_client_id(
            request=request,
            current_user=current_user
        )

        allowed = await rate_limiter.is_allowed(
            client_id=client_id,
            limit=limit,
            window=window
        )

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests"
            )

    return dependency

def ip_rate_limit(
    limit: int,
    window: int
):
    async def dependency(
        request: Request,
        rate_limiter: RateLimiter = Depends(
            get_rate_limiter
        )
    ):
        client_id = get_ip_client_id(
            request
        )

        allowed = await rate_limiter.is_allowed(
            client_id=client_id,
            limit=limit,
            window=window
        )

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests"
            )

    return dependency