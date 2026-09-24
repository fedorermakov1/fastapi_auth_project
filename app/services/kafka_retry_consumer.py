import asyncio

from confluent_kafka import Consumer

from app.core.config import settings
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

MAX_RETRIES = settings.MAX_RETRIES


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


def build_dlt_headers(
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
            "x-original-topic",
            "x-original-partition",
            "x-original-offset",
        }
    ]

    headers.extend([
        (
            "x-original-topic",
            message.topic().encode(),
        ),
        (
            "x-original-partition",
            str(message.partition()).encode(),
        ),
        (
            "x-original-offset",
            str(message.offset()).encode(),
        ),
        (
            "x-retry-count",
            str(retry_count).encode(),
        ),
        (
            "x-error",
            str(error).encode(),
        ),
    ])

    return headers


class KafkaRetryConsumer:
    def __init__(self):
        self.consumer = Consumer({
            "bootstrap.servers": (
                kafka_settings.KAFKA_BOOTSTRAP_SERVERS
            ),
            "group.id": "orders-retry-service",
            "enable.auto.commit": False,
            "auto.offset.reset": "earliest",
            "isolation.level": "read_committed",
        })

        self.consumer.subscribe([
            "orders.retry"
        ])

        self.transactional_producer = (
            KafkaTransactionalProducer(
                kafka_settings.KAFKA_BOOTSTRAP_SERVERS,
                "orders-retry-forward",
            )
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

    async def handle_error(
        self,
        message,
        error: Exception,
    ):
        retry_count = get_retry_count(
            message
        )

        next_retry_count = (
            retry_count + 1
        )

        if next_retry_count <= MAX_RETRIES:

            headers = build_retry_headers(
                message,
                next_retry_count,
                error,
            )

            self.transactional_producer.forward_with_offset(
                topic="orders.retry",
                key=message.key(),
                value=message.value(),
                headers=headers,
                source_message=message,
                consumer=self.consumer,
            )

            print(
                "KAFKA MESSAGE RETURNED TO RETRY: "
                f"partition={message.partition()}, "
                f"offset={message.offset()}, "
                f"retry_count={next_retry_count}"
            )

            return

        headers = build_dlt_headers(
            message,
            retry_count,
            error,
        )

        self.transactional_producer.forward_with_offset(
            topic="orders.dlq",
            key=message.key(),
            value=message.value(),
            headers=headers,
            source_message=message,
            consumer=self.consumer,
        )

        print(
            "KAFKA MESSAGE MOVED TO DLT: "
            f"partition={message.partition()}, "
            f"offset={message.offset()}, "
            f"retry_count={retry_count}"
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
                        "KAFKA RETRY CONSUMER ERROR: "
                        f"{message.error()}"
                    )
                    continue

                try:
                    await self.process_message(
                        message
                    )

                    self.consumer.commit(
                        message=message
                    )

                    print(
                        "KAFKA RETRY MESSAGE COMMITTED: "
                        f"partition={message.partition()}, "
                        f"offset={message.offset()}"
                    )

                except Exception as exc:

                    try:
                        await self.handle_error(
                            message,
                            exc,
                        )

                    except Exception as transaction_exc:
                        print(
                            "KAFKA RETRY/DLT "
                            "TRANSACTION ERROR: "
                            f"{type(transaction_exc).__name__}: "
                            f"{transaction_exc}"
                        )

        finally:
            self.consumer.close()
            self.transactional_producer.close()


async def main():
    stop_event = asyncio.Event()

    consumer = KafkaRetryConsumer()

    await consumer.consume(
        stop_event
    )


if __name__ == "__main__":
    asyncio.run(main())