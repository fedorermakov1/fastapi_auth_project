from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.processed_message_repository import ProcessedMessageRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.outbox_event_repository import OutboxEventRepository


class UnitOfWork:
    def __init__(self, db: AsyncSession):
        self.db = db

        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.tasks = TaskRepository(db)
        self.processed_messages = ProcessedMessageRepository(db)
        self.orders = OrderRepository(db)
        self.outbox_events = OutboxEventRepository(db)

    async def __aenter__(self):
        await self.db.begin()
        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        if exc_type:
            await self.db.rollback()
        else:
            if self.db.in_transaction():
                await self.db.commit()

    async def commit(self):
        await self.db.commit()

    async def rollback(self):
        await self.db.rollback()

    async def flush(self):
        await self.db.flush()