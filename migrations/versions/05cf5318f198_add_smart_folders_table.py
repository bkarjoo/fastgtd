"""Add smart folders table

Revision ID: 05cf5318f198
Revises: 565d3f6dc9c0
Create Date: 2025-08-30 11:26:01.520485

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '05cf5318f198'
down_revision: Union[str, None] = '565d3f6dc9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create node_smart_folders table
    op.create_table('node_smart_folders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rules', sa.JSON(), nullable=True),
        sa.Column('auto_refresh', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop node_smart_folders table
    op.drop_table('node_smart_folders')