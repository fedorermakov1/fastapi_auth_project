from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox_event import OutboxEvent


class OutboxEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(
            self,
            event_id: str,
            event_type: str,
            payload: dict,
            created_at: datetime,
    ) -> OutboxEvent:
        event = OutboxEvent(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            created_at=created_at,
        )

        self.db.add(event)

        return event

    async def get_unpublished_for_celery(
            self,
            limit: int = 100,
    ) -> list[OutboxEvent]:
        return await self._get_unpublished(
            OutboxEvent.celery_published_at,
            limit,
        )

    async def get_unpublished_for_kafka(
            self,
            limit: int = 100,
    ) -> list[OutboxEvent]:
        return await self._get_unpublished(
            OutboxEvent.kafka_published_at,
            limit,
        )

    async def _get_unpublished(
            self,
            published_column,
            limit: int,
    ) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(
                published_column.is_(None)
            )
            .order_by(
                OutboxEvent.created_at
            )
            .with_for_update(
                skip_locked=True
            )
            .limit(limit)
        )

        result = await self.db.execute(stmt)

        return result.scalars().all()