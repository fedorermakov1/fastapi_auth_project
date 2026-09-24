"""add cascade delete to refresh tokens

Revision ID: 65e1ae37e2db
Revises: 61f0221b785d
Create Date: 2026-08-26 13:23:16.541742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65e1ae37e2db'
down_revision: Union[str, Sequence[str], None] = '61f0221b785d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        op.f("refresh_tokens_user_id_fkey"),
        "refresh_tokens",
        type_="foreignkey",
    )

    op.create_foreign_key(
        op.f("refresh_tokens_user_id_fkey"),
        "refresh_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("refresh_tokens_user_id_fkey"),
        "refresh_tokens",
        type_="foreignkey",
    )

    op.create_foreign_key(
        op.f("refresh_tokens_user_id_fkey"),
        "refresh_tokens",
        "users",
        ["user_id"],
        ["id"],
    )
