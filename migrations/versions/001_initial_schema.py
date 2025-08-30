"""Initial schema - complete GTD database setup

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-08-30 11:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create complete GTD schema from scratch"""
    
    # Create users table
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
    
    # Create nodes table (enums will be auto-created by SQLAlchemy)
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
    op.create_index('ix_node_owner_sort', 'nodes', ['owner_id', 'sort_order'])
    op.create_index('ix_node_parent', 'nodes', ['parent_id'])
    op.create_index('ix_node_type', 'nodes', ['node_type'])
    op.create_index(op.f('ix_nodes_owner_id'), 'nodes', ['owner_id'])
    op.create_index(op.f('ix_nodes_parent_id'), 'nodes', ['parent_id'])
    
    # Create node_tasks table
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
    op.create_index('ix_task_due_at', 'node_tasks', ['due_at'])
    op.create_index('ix_task_priority', 'node_tasks', ['priority'])
    op.create_index('ix_task_status', 'node_tasks', ['status'])
    
    # Create node_notes table
    op.create_table('node_notes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['id'], ['nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create tags table
    op.create_table('tags',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', 'name', name='uq_tag_owner_name')
    )
    
    # Create node_tags association table
    op.create_table('node_tags',
        sa.Column('node_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('node_id', 'tag_id')
    )
    
    # Create smart folder support tables
    op.create_table('default_nodes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('node_type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_smart_folder', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('smart_folder_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', 'node_type', name='uq_default_node_owner_type')
    )


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('node_tags')
    op.drop_table('node_notes')
    op.drop_table('node_tasks')
    op.drop_table('default_nodes')
    op.drop_table('tags')
    op.drop_table('nodes')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS task_priority")
    op.execute("DROP TYPE IF EXISTS task_status")