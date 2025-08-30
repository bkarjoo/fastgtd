"""
Add default_task_lists table and seed defaults to system root per user

Revision ID: bb22cc33dd44
Revises: aa11bb22cc33
Create Date: 2025-08-19 00:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb22cc33dd44'
down_revision = 'aa11bb22cc33'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'default_task_lists',
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('task_list_id', sa.dialects.postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_list_id'], ['task_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
    )

    # Seed default to each user's system root
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        INSERT INTO default_task_lists (user_id, task_list_id, created_at, updated_at)
        SELECT u.id, tl.id, now(), now()
        FROM users u
        JOIN task_lists tl ON tl.owner_id = u.id AND tl.is_system_root = TRUE
        WHERE NOT EXISTS (
            SELECT 1 FROM default_task_lists d WHERE d.user_id = u.id
        )
        """
    ))


def downgrade() -> None:
    op.drop_table('default_task_lists')

