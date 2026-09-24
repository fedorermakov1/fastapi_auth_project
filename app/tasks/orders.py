from celery import Task
from sqlalchemy.exc import OperationalError

from app.celery_app import celery_app
from app.database.celery_session import create_celery_session_factory
from app.repositories.celery_order_processing_unit_of_work import (
    CeleryOrderProcessingUnitOfWork,
)


@celery_app.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def process_order_created(
        self: Task,
        event_id: str,
        order_id: int,
):
    SessionLocal = create_celery_session_factory()

    with SessionLocal() as db:
        with CeleryOrderProcessingUnitOfWork(db) as uow:
            created = uow.processed_messages.try_add(event_id)

            if not created:
                print(
                    f"Event {event_id} already processed"
                )
                return

            print(
                f"Processing order {order_id}, "
                f"event {event_id}, "
                f"retry={self.request.retries}"
            )

            uow.orders.update_status(
                order_id=order_id,
                status="processed",
            )