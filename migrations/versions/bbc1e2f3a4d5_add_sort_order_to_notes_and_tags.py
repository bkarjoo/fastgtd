"""add sort_order to notes and tags

Revision ID: bbc1e2f3a4d5
Revises: ab12cd34ef56
Create Date: 2025-08-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbc1e2f3a4d5'
down_revision: Union[str, None] = 'ab12cd34ef56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('notes', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tags', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))
    # Optional: drop server_default post backfill
    op.alter_column('notes', 'sort_order', server_default=None)
    op.alter_column('tags', 'sort_order', server_default=None)


def downgrade() -> None:
    op.drop_column('tags', 'sort_order')
    op.drop_column('notes', 'sort_order')

