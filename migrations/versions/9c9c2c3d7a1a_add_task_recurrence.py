"""add task recurrence

Revision ID: 9c9c2c3d7a1a
Revises: a1cc11c1af6e
Create Date: 2025-08-10 04:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c9c2c3d7a1a'
down_revision: Union[str, None] = 'b2f9d3f0e4a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('recurrence_rule', sa.Text(), nullable=True))
    op.add_column('tasks', sa.Column('recurrence_anchor', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('tasks', 'recurrence_anchor')
    op.drop_column('tasks', 'recurrence_rule')
