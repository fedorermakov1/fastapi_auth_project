import asyncio
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.database.session import SessionLocal
from app.repositories.unit_of_work import UnitOfWork


EVENT_TASKS = {
    "order.created": "app.tasks.orders.process_order_created",
}


async def publish_celery_outbox_events(
        stop_event: asyncio.Event,
):
    while not stop_event.is_set():

        async with SessionLocal() as db:
            uow = UnitOfWork(db)

            events = (
                await uow.outbox_events
                .get_unpublished_for_celery()
            )

            for event in events:
                try:
                    task_name = EVENT_TASKS[event.event_type]

                    await asyncio.to_thread(
                        celery_app.send_task,
                        task_name,
                        args=[
                            event.event_id,
                            event.payload["order_id"],
                        ],
                        queue="orders",
                        routing_key="order.created",
                    )

                    event.celery_published_at = (
                        datetime.now(timezone.utc)
                    )

                    await db.commit()

                except Exception as exc:
                    await db.rollback()

                    print(
                        "CELERY OUTBOX PUBLISH ERROR: "
                        f"{type(exc).__name__}: {exc}"
                    )

        await asyncio.sleep(1)