from app.repositories.unit_of_work import UnitOfWork
from app.schemas.events import Event

from app.services.events.handlers.order_created import (
    OrderCreatedHandler,
)


HANDLERS = {
    "order.created": OrderCreatedHandler,
}


class EventDispatcher:
    async def dispatch(
        self,
        event: Event,
        uow: UnitOfWork,
    ) -> None:
        handler_class = HANDLERS.get(event.event_type)

        if handler_class is None:
            raise ValueError(
                f"No handler for event type: {event.event_type}"
            )

        handler = handler_class(uow)

        await handler.handle(event)