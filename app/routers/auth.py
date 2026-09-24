from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.repositories.unit_of_work import UnitOfWork
from app.repositories.dependencies import get_uow

from app.services.auth_service import (
    refresh_access_token,
    logout,
    login
)

from app.schemas.auth import Token

from app.rate_limit.dependencies import ip_rate_limit

router = APIRouter(
    tags=["Auth"]
)


@router.post(
    "/token",
    response_model=Token,
    dependencies=[
        Depends(ip_rate_limit(5, 60))
    ]
)
async def login_user(
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        uow: UnitOfWork = Depends(get_uow, scope="function")
):
    tokens = await login(
        uow=uow,
        username=form_data.username,
        password=form_data.password
    )

    if tokens is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )

    return {
        "access_token": tokens.access_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
async def refresh(
        request: Request,
        response: Response,
        uow: UnitOfWork = Depends(get_uow, scope="function")
):
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token is None:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing"
        )

    tokens = await refresh_access_token(
        uow=uow,
        refresh_token=refresh_token
    )

    if tokens is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )

    return {
        "access_token": tokens.access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout_user(
        request: Request,
        response: Response,
        uow: UnitOfWork = Depends(get_uow, scope="function")
):
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token is None:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing"
        )

    await logout(
        uow=uow,
        refresh_token=refresh_token
    )

    response.delete_cookie(
        key="refresh_token"
    )

    return {
        "message": "Successfully logged out"
    }
