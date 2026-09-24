from pydantic import BaseModel

from app.schemas.events import (
    Event,
    OrderCreatedEvent,
)

EVENT_MODELS: dict[str, type[BaseModel]] = {
    "order.created": OrderCreatedEvent,
}


def parse_event(data: dict) -> Event:
    event_type = data["event_type"]

    event_model = EVENT_MODELS.get(event_type)

    if event_model is None:
        raise ValueError(
            f"Unknown event type: {event_type}"
        )

    return event_model.model_validate(data)
