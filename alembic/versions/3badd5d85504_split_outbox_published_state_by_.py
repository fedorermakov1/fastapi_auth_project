"""split outbox published state by transport

Revision ID: 3badd5d85504
Revises: c2f5edce35e9
Create Date: 2026-09-16 13:13:34.899101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3badd5d85504'
down_revision: Union[str, Sequence[str], None] = 'c2f5edce35e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "outbox_events",
        sa.Column(
            "celery_published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "outbox_events",
        sa.Column(
            "kafka_published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE outbox_events
        SET celery_published_at = published_at
        WHERE published_at IS NOT NULL
        """
    )

    op.drop_column(
        "outbox_events",
        "published_at",
    )


def downgrade() -> None:
    op.add_column(
        "outbox_events",
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE outbox_events
        SET published_at = celery_published_at
        WHERE celery_published_at IS NOT NULL
        """
    )

    op.drop_column(
        "outbox_events",
        "celery_published_at",
    )

    op.drop_column(
        "outbox_events",
        "kafka_published_at",
    )
