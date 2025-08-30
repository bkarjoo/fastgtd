"""
Add system roots for note_lists and default_note_lists mapping

Revision ID: cc33dd44ee55
Revises: bb22cc33dd44
Create Date: 2025-08-19 01:20:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'cc33dd44ee55'
down_revision = 'bb22cc33dd44'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add is_system_root to note_lists
    op.add_column('note_lists', sa.Column('is_system_root', sa.Boolean(), nullable=False, server_default=sa.false()))

    # 2) Create system root per user (no constraints yet)
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        INSERT INTO note_lists (id, owner_id, parent_list_id, name, description, sort_order, created_at, updated_at, is_system_root)
        SELECT gen_random_uuid(), u.id, NULL, '__NOTE_ROOT__', 'System note root', 0, NOW(), NOW(), TRUE
        FROM users u
        WHERE NOT EXISTS (
            SELECT 1 FROM note_lists nl WHERE nl.owner_id = u.id AND nl.is_system_root = TRUE
        )
        """
    ))

    # 3) Reparent existing top-level note lists to the system root
    conn.execute(sa.text(
        """
        UPDATE note_lists AS nl
        SET parent_list_id = root.id
        FROM (
            SELECT id, owner_id FROM note_lists WHERE is_system_root = TRUE
        ) AS root
        WHERE nl.owner_id = root.owner_id
          AND nl.is_system_root = FALSE
          AND nl.parent_list_id IS NULL
        """
    ))

    # 4) Now add partial unique index and the check constraint (data is compliant)
    op.create_index(
        'uq_notelist_owner_system_root',
        'note_lists',
        ['owner_id'],
        unique=True,
        postgresql_where=sa.text('is_system_root = true'),
    )
    op.create_check_constraint(
        'ck_notelist_parent_null_only_for_root',
        'note_lists',
        "(is_system_root AND parent_list_id IS NULL) OR (NOT is_system_root AND parent_list_id IS NOT NULL)",
    )

    # 5) Create default_note_lists table and seed to system root
    op.create_table(
        'default_note_lists',
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('note_list_id', sa.dialects.postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['note_list_id'], ['note_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
    )
    conn.execute(sa.text(
        """
        INSERT INTO default_note_lists (user_id, note_list_id, created_at, updated_at)
        SELECT u.id, nl.id, NOW(), NOW()
        FROM users u
        JOIN note_lists nl ON nl.owner_id = u.id AND nl.is_system_root = TRUE
        WHERE NOT EXISTS (
            SELECT 1 FROM default_note_lists d WHERE d.user_id = u.id
        )
        """
    ))


def downgrade() -> None:
    op.drop_table('default_note_lists')
    try:
        op.drop_index('uq_notelist_owner_system_root', table_name='note_lists')
    except Exception:
        pass
    try:
        op.drop_constraint('ck_notelist_parent_null_only_for_root', 'note_lists', type_='check')
    except Exception:
        pass
    try:
        op.drop_column('note_lists', 'is_system_root')
    except Exception:
        pass
