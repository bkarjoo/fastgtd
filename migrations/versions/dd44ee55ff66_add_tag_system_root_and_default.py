"""
Add system roots for tag_lists and default_tag_lists mapping

Revision ID: dd44ee55ff66
Revises: cc33dd44ee55
Create Date: 2025-08-19 02:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'dd44ee55ff66'
down_revision = 'cc33dd44ee55'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add is_system_root to tag_lists
    op.add_column('tag_lists', sa.Column('is_system_root', sa.Boolean(), nullable=False, server_default=sa.false()))

    conn = op.get_bind()
    # 2) Create system root per user
    conn.execute(sa.text(
        """
        INSERT INTO tag_lists (id, owner_id, parent_list_id, name, description, sort_order, created_at, updated_at, is_system_root)
        SELECT gen_random_uuid(), u.id, NULL, '__TAG_ROOT__', 'System tag root', 0, NOW(), NOW(), TRUE
        FROM users u
        WHERE NOT EXISTS (
            SELECT 1 FROM tag_lists tl WHERE tl.owner_id = u.id AND tl.is_system_root = TRUE
        )
        """
    ))

    # 3) Reparent existing top-level tag lists to system root
    conn.execute(sa.text(
        """
        UPDATE tag_lists AS tl
        SET parent_list_id = root.id
        FROM (
            SELECT id, owner_id FROM tag_lists WHERE is_system_root = TRUE
        ) AS root
        WHERE tl.owner_id = root.owner_id
          AND tl.is_system_root = FALSE
          AND tl.parent_list_id IS NULL
        """
    ))

    # 4) Now add partial unique index and check constraint
    op.create_index(
        'uq_taglist_owner_system_root',
        'tag_lists',
        ['owner_id'],
        unique=True,
        postgresql_where=sa.text('is_system_root = true'),
    )
    op.create_check_constraint(
        'ck_taglist_parent_null_only_for_root',
        'tag_lists',
        "(is_system_root AND parent_list_id IS NULL) OR (NOT is_system_root AND parent_list_id IS NOT NULL)",
    )

    # 5) Create default_tag_lists and seed to system root
    op.create_table(
        'default_tag_lists',
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('tag_list_id', sa.dialects.postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_list_id'], ['tag_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
    )
    conn.execute(sa.text(
        """
        INSERT INTO default_tag_lists (user_id, tag_list_id, created_at, updated_at)
        SELECT u.id, tl.id, NOW(), NOW()
        FROM users u
        JOIN tag_lists tl ON tl.owner_id = u.id AND tl.is_system_root = TRUE
        WHERE NOT EXISTS (
            SELECT 1 FROM default_tag_lists d WHERE d.user_id = u.id
        )
        """
    ))


def downgrade() -> None:
    op.drop_table('default_tag_lists')
    try:
        op.drop_index('uq_taglist_owner_system_root', table_name='tag_lists')
    except Exception:
        pass
    try:
        op.drop_constraint('ck_taglist_parent_null_only_for_root', 'tag_lists', type_='check')
    except Exception:
        pass
    try:
        op.drop_column('tag_lists', 'is_system_root')
    except Exception:
        pass

