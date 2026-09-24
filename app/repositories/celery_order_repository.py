from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order


class CeleryOrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def update_status(
            self,
            order_id: int,
            status: str
    ) -> None:
        stmt = select(Order).where(
            Order.id == order_id
        )

        result = self.db.execute(stmt)

        order = result.scalar_one_or_none()

        if order is None:
            raise ValueError(
                f"Order {order_id} not found"
            )

        order.status = status