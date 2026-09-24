from typing import Generic, TypeVar

from pydantic import BaseModel

PayloadT = TypeVar("PayloadT")


class Event(BaseModel, Generic[PayloadT]):
    event_id: str
    event_type: str
    payload: PayloadT


class OrderCreatedPayload(BaseModel):
    order_id: int
    status: str


class OrderCreatedEvent(Event[OrderCreatedPayload]):
    pass
