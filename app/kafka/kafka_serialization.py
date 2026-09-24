import json

from confluent_kafka.serialization import (
    MessageField,
    SerializationContext,
)
from confluent_kafka.schema_registry import (
    SchemaRegistryClient,
)
from confluent_kafka.schema_registry.json_schema import (
    JSONDeserializer,
    JSONSerializer,
)

from app.kafka.config import kafka_settings


ORDERS_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "event_id": {
            "type": "string"
        },
        "event_type": {
            "type": "string"
        },
        "payload": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer"
                },
                "status": {
                    "type": "string"
                }
            },
            "required": [
                "order_id",
                "status"
            ]
        }
    },
    "required": [
        "event_id",
        "event_type",
        "payload"
    ]
})


schema_registry = SchemaRegistryClient({
    "url": kafka_settings.SCHEMA_REGISTRY_URL
})


json_serializer = JSONSerializer(
    ORDERS_SCHEMA,
    schema_registry,
)


def from_dict(
    data: dict,
    ctx: SerializationContext,
):
    return data


json_deserializer = JSONDeserializer(
    ORDERS_SCHEMA,
    from_dict=from_dict,
    schema_registry_client=schema_registry,
)

def serialize_event(
    event: dict,
    topic: str,
) -> bytes:
    return json_serializer(
        event,
        SerializationContext(
            topic,
            MessageField.VALUE,
        ),
    )


def deserialize_event(
    data: bytes,
    topic: str,
) -> dict:
    return json_deserializer(
        data,
        SerializationContext(
            topic,
            MessageField.VALUE,
        ),
    )