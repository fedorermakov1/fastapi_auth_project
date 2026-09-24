from app.repositories.unit_of_work import UnitOfWork
from app.schemas.events import OrderCreatedEvent


class OrderCreatedHandler:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def handle(self, event: OrderCreatedEvent) -> None:
        await self.uow.orders.update_status(
            order_id=event.payload.order_id,
            status=event.payload.status,
        )
