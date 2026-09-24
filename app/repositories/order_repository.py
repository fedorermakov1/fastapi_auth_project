from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(
        self,
        status: str,
        created_at: datetime,
    ) -> Order:
        order = Order(
            status=status,
            created_at=created_at,
        )

        self.db.add(order)

        return order

    async def update_status(
            self,
            order_id: int,
            status: str
    ):
        stmt = select(Order).where(Order.id == order_id)

        result = await self.db.execute(stmt)

        order = result.scalar_one_or_none()

        if order is None:
            raise ValueError(f"Order {order_id} not found")

        order.status = status



