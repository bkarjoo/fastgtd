"""clean_slate_unified_nodes - Complete schema overhaul

Revision ID: clean_slate_unified_nodes
Revises: b8cf2fcac675
Create Date: 2025-08-21 21:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'clean_slate_unified_nodes'
down_revision: Union[str, None] = 'b8cf2fcac675'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Complete clean slate migration - drops all tables and recreates with unified schema"""
    
    # Drop all existing tables (test data only)
    op.execute("DROP SCHEMA IF EXISTS public CASCADE")
    op.execute("CREATE SCHEMA public")
    op.execute("GRANT ALL ON SCHEMA public TO public")
    
    # Create users table first
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create enums
    op.execute("CREATE TYPE task_status AS ENUM ('todo', 'in_progress', 'done', 'dropped')")
    op.execute("CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent')")
    
    # Create unified nodes table
    op.create_table('nodes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('node_type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['parent_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_node_owner_sort', 'nodes', ['owner_id', 'sort_order'], unique=False)
    op.create_index('ix_node_parent', 'nodes', ['parent_id'], unique=False)
    op.create_index('ix_node_type', 'nodes', ['node_type'], unique=False)
    op.create_index(op.f('ix_nodes_owner_id'), 'nodes', ['owner_id'], unique=False)
    op.create_index(op.f('ix_nodes_parent_id'), 'nodes', ['parent_id'], unique=False)
    
    # Create task-specific data table
    op.create_table('node_tasks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('todo', 'in_progress', 'done', 'dropped', name='task_status'), nullable=False, server_default='todo'),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'urgent', name='task_priority'), nullable=False, server_default='medium'),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('earliest_start_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('recurrence_rule', sa.Text(), nullable=True),
        sa.Column('recurrence_anchor', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_task_due_at', 'node_tasks', ['due_at'], unique=False)
    op.create_index('ix_task_priority', 'node_tasks', ['priority'], unique=False)
    op.create_index('ix_task_status', 'node_tasks', ['status'], unique=False)
    
    # Create note-specific data table
    op.create_table('node_notes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['id'], ['nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create minimal tags infrastructure for now (we'll expand this later)
    op.create_table('tags',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=32), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', 'name', name='uq_tag_owner_name')
    )
    
    # Create node-tags association
    op.create_table('node_tags',
        sa.Column('node_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('node_id', 'tag_id')
    )

    # Recreate alembic_version table
    op.create_table('alembic_version',
        sa.Column('version_num', sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint('version_num')
    )


def downgrade() -> None:
    """Not implemented - this is a one-way migration for clean slate"""
    raise NotImplementedError("This migration cannot be downgraded - it's a clean slate rebuild")