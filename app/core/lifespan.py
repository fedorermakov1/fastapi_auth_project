import asyncio
import json
from contextlib import asynccontextmanager

import aio_pika
import redis.asyncio as redis
from fastapi import FastAPI

from app.cache.cache import Cache
from app.core.config import settings
from app.kafka.config import kafka_settings
from app.database.session import SessionLocal
from app.rate_limit.factory import create_rate_limit_strategy
from app.rate_limit.limiter import RateLimiter
from app.repositories.unit_of_work import UnitOfWork
from app.services.celery_outbox_publisher import (
    publish_celery_outbox_events,
)
from app.services.kafka_outbox_publisher import (
    KafkaOutboxPublisher,
    publish_kafka_outbox_events,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # =========================
    # Redis
    # =========================

    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )

    strategy = create_rate_limit_strategy(
        settings.RATE_LIMIT_STRATEGY,
        redis_client,
    )

    rate_limiter = RateLimiter(
        strategy=strategy,
    )

    # =========================
    # RabbitMQ
    # =========================

    connection = await aio_pika.connect_robust(
        settings.RABBITMQ_URL
    )

    channel = await connection.channel()
    publish_channel = await connection.channel()

    await channel.set_qos(
        prefetch_count=10
    )

    exchange = await channel.declare_exchange(
        "orders",
        aio_pika.ExchangeType.DIRECT,
        durable=True,
    )

    retry_exchange = await publish_channel.declare_exchange(
        "orders.retry",
        aio_pika.ExchangeType.DIRECT,
        durable=True,
    )

    # =========================
    # Outbox publishers
    # =========================

    stop_event = asyncio.Event()

    kafka_publisher = KafkaOutboxPublisher(
        kafka_settings.KAFKA_BOOTSTRAP_SERVERS
    )

    # =========================
    # RabbitMQ consumer
    # =========================

    async def process_message(
            message: aio_pika.IncomingMessage,
    ):
        try:
            data = json.loads(
                message.body.decode()
            )

            event_id = data["event_id"]

            async with SessionLocal() as db:
                uow = UnitOfWork(db)

                async with db.begin():
                    created = (
                        await uow.processed_messages.try_add(
                            event_id
                        )
                    )

                    if not created:
                        print(
                            f"Event {event_id} already processed"
                        )
                    else:
                        print(
                            f"Processing event: {event_id}"
                        )

                        print(data)

                        # Бизнес-логика здесь

            await message.ack()

            print(
                f"Message {event_id} acknowledged"
            )

        except json.JSONDecodeError as exc:
            print(
                f"Invalid message: {exc}"
            )

            await message.reject(
                requeue=False
            )

        except Exception as exc:
            retry_count = message.headers.get(
                "x-retry-count",
                0,
            )

            print(
                f"Message processing failed: "
                f"retry_count={retry_count}, "
                f"error={exc}"
            )

            if retry_count < settings.MAX_RETRIES:
                retry_message = aio_pika.Message(
                    body=message.body,
                    headers={
                        "x-retry-count": retry_count + 1,
                    },
                    delivery_mode=(
                        aio_pika.DeliveryMode.PERSISTENT
                    ),
                )

                try:
                    print(
                        "BEFORE RETRY PUBLISH"
                    )

                    await retry_exchange.publish(
                        retry_message,
                        routing_key="order.retry",
                        timeout=5,
                    )

                    print(
                        "AFTER RETRY PUBLISH"
                    )

                except Exception as publish_exc:
                    print(
                        "RETRY PUBLISH ERROR: "
                        f"{type(publish_exc).__name__}: "
                        f"{publish_exc}"
                    )

                    raise

                await message.ack()

            else:
                await message.reject(
                    requeue=False
                )

    queue = await channel.declare_queue(
        "order_queue",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "orders.dlx",
            "x-dead-letter-routing-key": "order.failed",
        },
    )

    await queue.bind(
        exchange,
        routing_key="order.created",
    )

    await queue.consume(
        process_message
    )

    # =========================
    # Start Outbox publishers
    # =========================

    celery_publisher_task = asyncio.create_task(
        publish_celery_outbox_events(
            stop_event=stop_event,
        )
    )

    kafka_publisher_task = asyncio.create_task(
        publish_kafka_outbox_events(
            stop_event=stop_event,
            publisher=kafka_publisher,
        )
    )

    # =========================
    # App state
    # =========================

    app.state.connection = connection
    app.state.channel = channel
    app.state.publish_channel = publish_channel

    app.state.exchange = exchange
    app.state.retry_exchange = retry_exchange

    app.state.celery_outbox_publisher = (
        celery_publisher_task
    )

    app.state.kafka_outbox_publisher = (
        kafka_publisher_task
    )

    app.state.kafka_publisher = kafka_publisher

    app.state.outbox_stop_event = stop_event

    app.state.redis = redis_client

    cache = Cache(redis_client)

    app.state.cache = cache
    app.state.rate_limiter = rate_limiter

    print(
        "=== REDIS CLIENT CREATED ==="
    )

    print(
        "=== CACHE CREATED ==="
    )

    # =========================
    # Application running
    # =========================

    yield

    # =========================
    # Shutdown
    # =========================

    stop_event.set()

    await celery_publisher_task
    await kafka_publisher_task

    await asyncio.to_thread(
        kafka_publisher.flush
    )

    await connection.close()

    await redis_client.aclose()

    print(
        "=== REDIS CLIENT CLOSED ==="
    )
