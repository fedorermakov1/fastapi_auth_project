from sqlalchemy.orm import Session

from app.repositories.celery_order_repository import (
    CeleryOrderRepository
)
from app.repositories.celery_processed_message_repository import (
    CeleryProcessedMessageRepository
)


class CeleryOrderProcessingUnitOfWork:
    def __init__(self, db: Session):
        self.db = db

        self.orders = CeleryOrderRepository(db)
        self.processed_messages = (
            CeleryProcessedMessageRepository(db)
        )

    def __enter__(self):
        self.db.begin()
        return self

    def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
    ):
        if exc_type:
            self.db.rollback()
        elif self.db.in_transaction():
            self.db.commit()

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def flush(self):
        self.db.flush()