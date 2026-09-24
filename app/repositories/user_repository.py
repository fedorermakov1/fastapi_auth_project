from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class UserRepository:

    def __init__(
        self,
        db: AsyncSession
    ):
        self.db = db

    async def get_by_username(
        self,
        username: str
    ):
        stmt = select(User).where(
            User.username == username
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str
    ):
        stmt = select(User).where(
            User.email == email
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        user_id: int
    ):
        return await self.db.get(
            User,
            user_id
        )

    async def get_all(self):
        stmt = select(User)

        result = await self.db.execute(stmt)

        return result.scalars().all()

    def create(
        self,
        username: str,
        email: str,
        hashed_password: str
    ):
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )

        self.db.add(user)

        return user

    async def delete(
            self,
            user: User
    ):
        await self.db.delete(user)