from typing import Protocol

from app.schemas.events import Event, OrderCreatedEvent


class EventHandler(Protocol):
    async def handle(self, event: Event) -> Event:
        pass

