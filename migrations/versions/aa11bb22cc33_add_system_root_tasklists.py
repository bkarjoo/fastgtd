"""
Add system root task lists and enforce parenting constraints

Revision ID: aa11bb22cc33
Revises: bbc1e2f3a4d5
Create Date: 2025-08-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'aa11bb22cc33'
down_revision = 'bbc1e2f3a4d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add is_system_root column with default false
    op.add_column(
        'task_lists',
        sa.Column('is_system_root', sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    bind = op.get_bind()

    # 2) Create a per-user system root row (if not present)
    # Name is a sentinel; users never see or interact with it via API
    # Note: Using SQL to avoid ORM dependencies in migrations
    bind.execute(text(
        """
        INSERT INTO task_lists (id, owner_id, parent_list_id, name, description, sort_order, created_at, updated_at, is_system_root)
        SELECT gen_random_uuid(), u.id, NULL, '__ROOT__', 'System root', 0, NOW(), NOW(), TRUE
        FROM users u
        WHERE NOT EXISTS (
            SELECT 1 FROM task_lists tl WHERE tl.owner_id = u.id AND tl.is_system_root = TRUE
        )
        """
    ))

    # 3) Reparent any existing top-level lists to the new system root
    bind.execute(text(
        """
        UPDATE task_lists AS tl
        SET parent_list_id = root.id
        FROM (
            SELECT id, owner_id FROM task_lists WHERE is_system_root = TRUE
        ) AS root
        WHERE tl.owner_id = root.owner_id
          AND tl.is_system_root = FALSE
          AND tl.parent_list_id IS NULL
        """
    ))

    # 4) Partial unique index to enforce exactly one system root per owner
    op.create_index(
        'uq_tasklist_owner_system_root',
        'task_lists',
        ['owner_id'],
        unique=True,
        postgresql_where=sa.text('is_system_root = true'),
    )

    # 5) Add check constraint already present in model (idempotent for DB)
    # In case it isn't already created by autogenerate, ensure here
    op.create_check_constraint(
        'ck_tasklist_parent_null_only_for_root',
        'task_lists',
        "(is_system_root AND parent_list_id IS NULL) OR (NOT is_system_root AND parent_list_id IS NOT NULL)",
    )


def downgrade() -> None:
    bind = op.get_bind()

    # 1) Drop the check and partial unique index first
    try:
        op.drop_constraint('ck_tasklist_parent_null_only_for_root', 'task_lists', type_='check')
    except Exception:
        pass
    try:
        op.drop_index('uq_tasklist_owner_system_root', table_name='task_lists')
    except Exception:
        pass

    # 2) Best-effort: set parent_list_id = NULL for lists whose parent is a system root
    bind.execute(text(
        """
        UPDATE task_lists tl
        SET parent_list_id = NULL
        WHERE tl.parent_list_id IN (
            SELECT id FROM task_lists WHERE is_system_root = TRUE
        )
        """
    ))

    # 3) Delete system root rows
    bind.execute(text("DELETE FROM task_lists WHERE is_system_root = TRUE"))

    # 4) Drop the column
    try:
        op.drop_column('task_lists', 'is_system_root')
    except Exception:
        pass
