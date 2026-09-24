import asyncio

from confluent_kafka import Consumer

from app.database.session import SessionLocal
from app.kafka.config import kafka_settings
from app.repositories.unit_of_work import UnitOfWork
from app.services.events.dispatcher import EventDispatcher
from app.services.events.parser import parse_event
from app.kafka.kafka_serialization import deserialize_event
from app.services.kafka_transactional import (
    KafkaTransactionalProducer,
)


dispatcher = EventDispatcher()


def get_retry_count(message) -> int:
    headers = dict(message.headers() or [])

    value = headers.get("x-retry-count")

    if value is None:
        return 0

    return int(value.decode())


def build_retry_headers(
    message,
    retry_count: int,
    error: Exception,
):
    headers = [
        header
        for header in (message.headers() or [])
        if header[0] not in {
            "x-retry-count",
            "x-error",
        }
    ]

    headers.append(
        (
            "x-retry-count",
            str(retry_count).encode(),
        )
    )

    headers.append(
        (
            "x-error",
            str(error).encode(),
        )
    )

    return headers


class KafkaOrderConsumer:
    def __init__(self):
        self.consumer = Consumer({
            "bootstrap.servers": (
                kafka_settings.KAFKA_BOOTSTRAP_SERVERS
            ),
            "group.id": kafka_settings.KAFKA_GROUP_ID,
            "enable.auto.commit": False,
            "auto.offset.reset": "earliest",
            "isolation.level": "read_committed",
        })

        self.consumer.subscribe(["orders"])

        self.retry_producer = KafkaTransactionalProducer(
            kafka_settings.KAFKA_BOOTSTRAP_SERVERS,
            "orders-main-retry",
        )

    async def process_message(self, message):
        raw_event = deserialize_event(
            message.value(),
            message.topic(),
        )

        event = parse_event(raw_event)

        async with SessionLocal() as db:
            async with UnitOfWork(db) as uow:

                is_new = (
                    await uow.processed_messages.try_add(
                        event.event_id
                    )
                )

                if not is_new:
                    print(
                        "Event already processed: "
                        f"{event.event_id}"
                    )
                    return

                await dispatcher.dispatch(
                    event,
                    uow,
                )

    async def consume(
        self,
        stop_event: asyncio.Event,
    ):
        try:
            while not stop_event.is_set():

                message = await asyncio.to_thread(
                    self.consumer.poll,
                    1.0,
                )

                if message is None:
                    continue

                if message.error():
                    print(
                        "KAFKA CONSUMER ERROR: "
                        f"{message.error()}"
                    )
                    continue

                try:
                    await self.process_message(message)

                    self.consumer.commit(
                        message=message
                    )

                    print(
                        "KAFKA MESSAGE COMMITTED: "
                        f"partition={message.partition()}, "
                        f"offset={message.offset()}"
                    )

                except Exception as exc:

                    retry_count = get_retry_count(
                        message
                    )

                    next_retry_count = (
                        retry_count + 1
                    )

                    headers = build_retry_headers(
                        message,
                        next_retry_count,
                        exc,
                    )

                    try:
                        self.retry_producer.forward_with_offset(
                            topic="orders.retry",
                            key=message.key(),
                            value=message.value(),
                            headers=headers,
                            source_message=message,
                            consumer=self.consumer,
                        )

                        print(
                            "KAFKA MESSAGE MOVED TO RETRY: "
                            f"partition={message.partition()}, "
                            f"offset={message.offset()}, "
                            f"retry_count={next_retry_count}"
                        )

                    except Exception as retry_exc:
                        print(
                            "KAFKA RETRY TRANSACTION ERROR: "
                            f"{type(retry_exc).__name__}: "
                            f"{retry_exc}"
                        )

        finally:
            self.consumer.close()
            self.retry_producer.close()


async def main():
    stop_event = asyncio.Event()

    consumer = KafkaOrderConsumer()

    await consumer.consume(
        stop_event
    )


if __name__ == "__main__":
    asyncio.run(main())