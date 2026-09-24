from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import RefreshToken

from app.core.security import (
    verify_refresh_token,
    get_refresh_token_hash
)


class RefreshTokenRepository:

    def __init__(
            self,
            db: AsyncSession
    ):
        self.db = db

    async def get_by_token(
            self,
            token: str
    ):
        try:
            token_id, secret = token.split(".", 1)
            token_id = UUID(token_id)
        except (ValueError, AttributeError):
            return None

        stmt = (
            select(RefreshToken)
            .options(joinedload(RefreshToken.user))
            .where(RefreshToken.token_id == token_id)
        )

        result = await self.db.execute(stmt)

        token_record = result.scalar_one_or_none()

        if token_record is None:
            return None

        if not verify_refresh_token(
                secret,
                token_record.token_hash
        ):
            return None

        if token_record.revoked:
            return None

        if token_record.expires_at < datetime.now(timezone.utc):
            return None

        return token_record


    def create(
            self,
            user_id: int,
            token_id: UUID,
            secret: str,
            expires_at: datetime
    ):
        refresh_token = RefreshToken(
            user_id=user_id,
            token_id=token_id,
            token_hash=get_refresh_token_hash(secret),
            expires_at=expires_at
        )

        self.db.add(refresh_token)

        return refresh_token


    def revoke(
            self,
            refresh_token: RefreshToken
    ):
        refresh_token.revoked = True
