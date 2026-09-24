import asyncio
from datetime import datetime, timezone

from confluent_kafka import Producer

from app.database.session import SessionLocal
from app.repositories.unit_of_work import UnitOfWork
from app.kafka.kafka_serialization import serialize_event


class KafkaOutboxPublisher:
    def __init__(self, bootstrap_servers: str):
        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "enable.idempotence": True,
            "acks": "all",
        })

    def publish(
        self,
        topic: str,
        key: str,
        event_id: str,
        event_type: str,
        payload: dict,
    ) -> None:

        delivery_error = None

        def delivery_report(err, msg):
            nonlocal delivery_error

            if err is not None:
                delivery_error = err

        message = {
            "event_id": event_id,
            "event_type": event_type,
            "payload": payload,
        }

        data = serialize_event(
            message,
            topic,
        )

        self.producer.produce(
            topic=topic,
            key=key,
            value=data,
            callback=delivery_report,
        )

        self.producer.flush()

        if delivery_error is not None:
            raise RuntimeError(
                f"Kafka delivery failed: {delivery_error}"
            )

    def flush(self) -> None:
        self.producer.flush()


async def publish_kafka_outbox_events(
    stop_event: asyncio.Event,
    publisher: KafkaOutboxPublisher,
):
    while not stop_event.is_set():

        async with SessionLocal() as db:
            uow = UnitOfWork(db)

            events = (
                await uow.outbox_events
                .get_unpublished_for_kafka()
            )

            for event in events:
                try:
                    await asyncio.to_thread(
                        publisher.publish,
                        "orders",
                        str(event.payload["order_id"]),
                        event.event_id,
                        event.event_type,
                        event.payload,
                    )

                    event.kafka_published_at = (
                        datetime.now(timezone.utc)
                    )

                    await db.commit()

                except Exception as exc:
                    await db.rollback()

                    print(
                        "KAFKA OUTBOX PUBLISH ERROR: "
                        f"{type(exc).__name__}: {exc}"
                    )

        await asyncio.sleep(1)