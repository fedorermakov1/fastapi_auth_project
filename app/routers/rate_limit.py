from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_rate_limiter
from app.rate_limit.limiter import RateLimiter

router = APIRouter(
    prefix="/rate-test",
    tags=["Rate Limit Test"]
)

@router.get("/")
async def rate_test(
    rate_limiter: RateLimiter = Depends(
        get_rate_limiter
    )
):
    allowed = await rate_limiter.is_allowed(
        "client_1"
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many requests"
        )

    return {
        "message": "Allowed"
    }