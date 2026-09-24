from datetime import datetime, timezone
from uuid import uuid4

from app.models.order import Order
from app.repositories.unit_of_work import UnitOfWork


async def create_order(
        uow: UnitOfWork
) -> Order:
    event_id = str(uuid4())

    order = await uow.orders.add(
        status="created",
        created_at=datetime.now(timezone.utc)
    )

    await uow.flush()

    await uow.outbox_events.add(
        event_id=event_id,
        event_type="order.created",
        payload={
            "order_id": order.id,
            "status": order.status,
        },
        created_at=datetime.now(timezone.utc)
    )

    return order