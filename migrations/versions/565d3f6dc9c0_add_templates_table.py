"""Add templates table

Revision ID: 565d3f6dc9c0
Revises: 001_initial_schema
Create Date: 2025-08-30 11:05:14.473308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '565d3f6dc9c0'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create node_templates table
    op.create_table('node_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on category for filtering
    op.create_index(op.f('ix_node_templates_category'), 'node_templates', ['category'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_node_templates_category'), table_name='node_templates')
    
    # Drop table
    op.drop_table('node_templates')