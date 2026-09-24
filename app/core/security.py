from uuid import uuid4

from pwdlib import PasswordHash

import secrets

from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings

from fastapi.security import OAuth2PasswordBearer

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token"
)

def create_refresh_token():
    secret = secrets.token_hex(64)
    token_id = uuid4()

    return f"{token_id}.{secret}"

def get_refresh_token_hash(token: str) -> str:
    return password_hash.hash(token)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def verify_refresh_token(
        token: str,
        token_hash: str,
) -> bool:
    return password_hash.verify(token, token_hash)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
        data: dict,
        expires_delta: timedelta | None = None
):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt

