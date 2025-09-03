"""Add create_container field to templates

Revision ID: d33e6481681d
Revises: 9a4d762bd8f1
Create Date: 2025-09-01 20:35:12.476477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd33e6481681d'
down_revision: Union[str, None] = '9a4d762bd8f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add create_container field to node_templates table
    op.add_column('node_templates', 
        sa.Column('create_container', sa.Boolean(), nullable=False, server_default='true')
    )


def downgrade() -> None:
    # Remove create_container column
    op.drop_column('node_templates', 'create_container')

