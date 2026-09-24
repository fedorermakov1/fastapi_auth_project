import json

from confluent_kafka import Producer

from app.kafka.config import kafka_settings


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")
        return

    print(
        f"Delivered: "
        f"topic={msg.topic()}, "
        f"partition={msg.partition()}, "
        f"offset={msg.offset()}, "
        f"key={msg.key()}"
    )


producer = Producer(
    {
        "bootstrap.servers": kafka_settings.KAFKA_BOOTSTRAP_SERVERS,
        "enable.idempotence": True,
    }
)


event = {
    "event_id": "python-1",
    "order_id": 42,
    "event_type": "order.created",
}


producer.produce(
    topic="orders",
    key=str(event["order_id"]),
    value=json.dumps(event),
    callback=delivery_report,
)

producer.flush()