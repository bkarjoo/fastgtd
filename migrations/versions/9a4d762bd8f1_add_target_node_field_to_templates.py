"""Add target_node field to templates

Revision ID: 9a4d762bd8f1
Revises: 5fb08eb988ac
Create Date: 2025-09-01 20:10:41.025346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a4d762bd8f1'
down_revision: Union[str, None] = '5fb08eb988ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add target_node field to node_templates table
    op.add_column('node_templates', 
        sa.Column('target_node_id', sa.UUID(), nullable=True)
    )
    
    # Add foreign key constraint to nodes table
    op.create_foreign_key(
        'fk_node_templates_target_node',
        'node_templates', 'nodes',
        ['target_node_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_node_templates_target_node', 'node_templates', type_='foreignkey')
    
    # Remove target_node_id column
    op.drop_column('node_templates', 'target_node_id')

