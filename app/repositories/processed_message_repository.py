from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processed_message import ProcessedMessage


class ProcessedMessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def try_add(self, event_id: str) -> bool:
        stmt = (
            insert(ProcessedMessage)
            .values(
                event_id=event_id,
                processed_at=datetime.now(timezone.utc),
            )
            .on_conflict_do_nothing(
                index_elements=["event_id"]
            )
            .returning(ProcessedMessage.id)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none() is not None
