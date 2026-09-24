from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Task


class TaskRepository:

    def __init__(
            self,
            db: AsyncSession
    ):
        self.db = db

    async def get_by_id(
            self,
            task_id: int,
            user_id: int
    ) -> Task | None:

        stmt = (
            select(Task)
            .options(
                joinedload(Task.user)
            )
            .where(
                Task.id == task_id,
                Task.user_id == user_id
            )
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_all_by_user(
            self,
            user_id: int
    ) -> list[Task]:

        stmt = (
            select(Task)
            .options(
                joinedload(Task.user)
            )
            .where(
                Task.user_id == user_id
            )
            .order_by(
                Task.created_at.desc()
            )
        )

        result = await self.db.execute(stmt)

        return result.scalars().all()

    def create(
            self,
            title: str,
            description: str | None,
            user_id: int
    ):
        task = Task(
            title=title,
            description=description,
            user_id=user_id
        )

        self.db.add(task)

        return task

    async def delete(
            self,
            task: Task
    ):
        await self.db.delete(task)
