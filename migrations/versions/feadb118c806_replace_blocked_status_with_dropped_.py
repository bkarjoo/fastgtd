"""Replace blocked status with dropped status in TaskStatus enum

Revision ID: feadb118c806
Revises: ee55ff66aabb
Create Date: 2025-08-19 16:27:34.406834

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'feadb118c806'
down_revision: Union[str, None] = 'ee55ff66aabb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new 'dropped' value to the TaskStatus enum
    op.execute("ALTER TYPE task_status ADD VALUE 'dropped'")
    
    # Remove the old 'blocked' value from the TaskStatus enum
    # Note: PostgreSQL doesn't allow removing enum values directly,
    # but since we confirmed no tasks use 'blocked', we can leave it
    # as an unused value, or recreate the enum if needed in the future


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values,
    # so we can't easily downgrade this migration.
    # In a downgrade, you would need to recreate the enum entirely.
    pass

