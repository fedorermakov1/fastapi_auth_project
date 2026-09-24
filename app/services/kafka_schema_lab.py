from confluent_kafka import Producer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from confluent_kafka import Consumer
from confluent_kafka.schema_registry.json_schema import JSONDeserializer


schema_registry = SchemaRegistryClient({
    "url": "http://schema-registry:8081"
})


schema_str = """
{
  "type": "object",
  "properties": {
    "event_id": {
      "type": "integer"
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
        },
        "currency": {
          "type": "string",
          "default": "USD"
}
      },
      "required": ["order_id", "status"]
    }
  },
  "required": ["event_id", "event_type", "payload"]
}
"""


serializer = JSONSerializer(
    schema_str,
    schema_registry,
)


producer = Producer({
    "bootstrap.servers": "kafka:29092"
})


event = {
    "event_id": 1,
    "event_type": "order_created",
    "payload": {
        "order_id": 100,
        "status": "created"
    }
}


data = serializer(
    event,
    SerializationContext(
        "orders-schema-lab",
        MessageField.VALUE,
    ),
)


producer.produce(
    topic="orders-schema-lab",
    value=data,
)

producer.flush()

print("EVENT SENT")

deserializer = JSONDeserializer(
    schema_str,
    schema_registry,
)

consumer = Consumer({
    "bootstrap.servers": "kafka:29092",
    "group.id": "kafka-schema-lab",
    "auto.offset.reset": "earliest",
})

consumer.subscribe(["orders-schema-lab"])

message = consumer.poll(5.0)

value = deserializer(
    message.value(),
    SerializationContext(
        message.topic(),
        MessageField.VALUE,
    ),
)

print(value)