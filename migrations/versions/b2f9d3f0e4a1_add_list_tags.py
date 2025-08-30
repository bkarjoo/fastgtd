"""add list_tags association

Revision ID: b2f9d3f0e4a1
Revises: a1cc11c1af6e
Create Date: 2025-08-10 04:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f9d3f0e4a1'
down_revision: Union[str, None] = 'a1cc11c1af6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'list_tags',
        sa.Column('list_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['list_id'], ['task_lists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('list_id', 'tag_id'),
    )


def downgrade() -> None:
    op.drop_table('list_tags')

