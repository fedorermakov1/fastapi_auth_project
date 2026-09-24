"""add token id to refresh tokens

Revision ID: f69a8886a91a
Revises: 65e1ae37e2db
Create Date: 2026-09-03 12:13:04.380622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f69a8886a91a'
down_revision: Union[str, Sequence[str], None] = '65e1ae37e2db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        'refresh_tokens',
        sa.Column(
            'token_id',
            sa.Uuid(),
            nullable=True
        )
    )

    op.execute(
        """
        UPDATE refresh_tokens
        SET token_id = gen_random_uuid()
        WHERE token_id IS NULL
        """
    )

    op.alter_column(
        'refresh_tokens',
        'token_id',
        nullable=False
    )

    op.drop_constraint(
        op.f('refresh_tokens_token_hash_key'),
        'refresh_tokens',
        type_='unique'
    )

    op.create_index(
        op.f('ix_refresh_tokens_token_id'),
        'refresh_tokens',
        ['token_id'],
        unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f('ix_refresh_tokens_token_id'),
        table_name='refresh_tokens'
    )

    op.create_unique_constraint(
        op.f('refresh_tokens_token_hash_key'),
        'refresh_tokens',
        ['token_hash'],
        postgresql_nulls_not_distinct=False
    )

    op.drop_column(
        'refresh_tokens',
        'token_id'
    )