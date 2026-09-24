from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.order_repository import OrderRepository
from app.repositories.processed_message_repository import (
    ProcessedMessageRepository
)


class OrderProcessingUnitOfWork:
    def __init__(self, db: AsyncSession):
        self.db = db

        self.orders = OrderRepository(db)
        self.processed_messages = ProcessedMessageRepository(db)

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
        elif self.db.in_transaction():
            await self.db.commit()

    async def commit(self):
        await self.db.commit()

    async def rollback(self):
        await self.db.rollback()

    async def flush(self):
        await self.db.flush()