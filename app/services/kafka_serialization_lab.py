from confluent_kafka import Producer
from confluent_kafka.serialization import (
    SerializationContext,
    StringSerializer,
)
from confluent_kafka.serialization import MessageField


serializer = StringSerializer("utf_8")

producer = Producer(
    {
        "bootstrap.servers": "kafka:29092",
    }
)

topic = "kafka-serialization-lab"

value = serializer(
    "hello kafka",
    SerializationContext(
        topic,
        MessageField.VALUE,
    ),
)

producer.produce(
    topic=topic,
    value=value,
)

producer.flush()