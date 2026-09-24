from confluent_kafka import Consumer
from app.kafka.config import kafka_settings


consumer = Consumer({
    "bootstrap.servers": kafka_settings.KAFKA_BOOTSTRAP_SERVERS,
    "group.id": kafka_settings.KAFKA_GROUP_ID,
    "enable.auto.commit": False,
    "auto.offset.reset": "earliest"

})

consumer.subscribe(["orders"])

while True:
    msg = consumer.poll(1.0)

    if msg is None:
        continue

    if msg.error():
        print(f"Kafka error: {msg.error()}")
        continue

    print(
        f"topic={msg.topic()} "
        f"partition={msg.partition()} "
        f"offset={msg.offset()} "
        f"key={msg.key()} "
        f"value={msg.value()}"
    )

    consumer.commit(message=msg)