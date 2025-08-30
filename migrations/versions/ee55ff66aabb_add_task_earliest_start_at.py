"""
Add earliest_start_at to tasks for postponement

Revision ID: ee55ff66aabb
Revises: dd44ee55ff66
Create Date: 2025-08-19 02:15:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'ee55ff66aabb'
down_revision = 'dd44ee55ff66'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('earliest_start_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    try:
        op.drop_column('tasks', 'earliest_start_at')
    except Exception:
        pass

