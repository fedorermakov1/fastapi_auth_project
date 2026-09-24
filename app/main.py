from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

from prometheus_client import generate_latest
from app.monitoring.metrics import registry

from sqlalchemy.exc import IntegrityError

from app.routers.users import router as users_router
from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router
from app.routers.rate_limit import router as rate_limit_router
from app.routers.dev import router as dev_router
from app.routers.orders import router as orders_router

from app.core.exceptions import (
    EmailAlreadyExists,
    UsernameAlreadyExists
)

from app.middleware.request import request_middleware

from app.core.logging import setup_logging
from app.core.lifespan import lifespan


app = FastAPI(lifespan=lifespan)
setup_logging()

app.middleware("http")(request_middleware)

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(rate_limit_router)
app.include_router(dev_router)
app.include_router(orders_router)


@app.get("/metrics")
async def metrics():
    data = generate_latest(registry)

    return Response(
        content=data,
        media_type="text/plain",
    )

@app.exception_handler(EmailAlreadyExists)
async def email_exists_handler(request, exc):

    return JSONResponse(
        status_code=409,
        content={
            "detail": "Email already registered"
        }
    )

@app.exception_handler(UsernameAlreadyExists)
async def username_exists_handler(request, exc):

    return JSONResponse(
        status_code=409,
        content={
            "detail": "Username already taken"
        }
    )

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc):
    message = str(exc.orig)

    if "users_email_key" in message:
        detail = "Email already registered"

    elif "users_username_key" in message:
        detail = "Username already taken"

    else:
        detail = "Database error"

    return JSONResponse(
        status_code=409,
        content={
            "detail": detail
        }
    )






