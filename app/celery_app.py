from celery import Celery
from kombu import Exchange, Queue

from app.core.celery_config import celery_settings


orders_dlx = Exchange(
    "orders_dlx",
    type="direct",
)

orders_dlq = Queue(
    "orders_dlq",
    orders_dlx,
    routing_key="order.failed",
)


celery_app = Celery(
    "fastapi_auth_project",
    broker=celery_settings.RABBITMQ_URL,
    backend=celery_settings.REDIS_URL,
    include=[
        "app.tasks.example",
        "app.tasks.orders",
    ],
)

celery_app.conf.update(
    control_queue_exclusive=True,
    event_queue_exclusive=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    task_acks_on_failure_or_timeout=False,

    task_queues=(
        Queue(
            "calculations",
            Exchange("calculations", type="direct"),
            routing_key="calculations",
        ),

        Queue(
            "emails",
            Exchange("emails", type="direct"),
            routing_key="emails",
        ),

        Queue(
            "orders",
            Exchange("celery_orders", type="direct"),
            routing_key="order.created",
            queue_arguments={
                "x-dead-letter-exchange": "orders_dlx",
                "x-dead-letter-routing-key": "order.failed",
            },
        ),

        orders_dlq,
    ),

    task_routes={
        "app.tasks.example.add": {
            "queue": "calculations",
            "routing_key": "calculations",
        },
        "app.tasks.example.send_email": {
            "queue": "emails",
            "routing_key": "emails",
        },
        "app.tasks.example.broken_task": {
            "queue": "calculations",
            "routing_key": "calculations",
        },
        "app.tasks.orders.process_order_created": {
            "queue": "orders",
            "routing_key": "order.created",
        },
    },
)