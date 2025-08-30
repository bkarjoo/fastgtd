"""add_hierarchical_structure_and_note_lists

Revision ID: f67fef330ae9
Revises: c3d5e6f7a8b9
Create Date: 2025-08-14 19:47:35.235591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f67fef330ae9'
down_revision: Union[str, None] = 'c3d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add hierarchy support to existing containers
    # Add parent_list_id to task_lists
    op.add_column('task_lists', sa.Column('parent_list_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_task_lists_parent_list_id'), 'task_lists', ['parent_list_id'], unique=False)
    op.create_foreign_key(
        'fk_task_lists_parent_list_id_task_lists', 'task_lists', 'task_lists', 
        ['parent_list_id'], ['id'], ondelete='CASCADE'
    )
    
    # Add parent_list_id to tag_lists
    op.add_column('tag_lists', sa.Column('parent_list_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_tag_lists_parent_list_id'), 'tag_lists', ['parent_list_id'], unique=False)
    op.create_foreign_key(
        'fk_tag_lists_parent_list_id_tag_lists', 'tag_lists', 'tag_lists',
        ['parent_list_id'], ['id'], ondelete='CASCADE'
    )
    
    # Add parent_id to tags (for tag hierarchy)
    op.add_column('tags', sa.Column('parent_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_tags_parent_id'), 'tags', ['parent_id'], unique=False)
    op.create_foreign_key(
        'fk_tags_parent_id_tags', 'tags', 'tags',
        ['parent_id'], ['id'], ondelete='CASCADE'
    )
    
    # 2. Create note_lists table
    op.create_table(
        'note_lists',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('parent_list_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['parent_list_id'], ['note_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', 'name', name='uq_notelist_owner_name')
    )
    op.create_index(op.f('ix_note_lists_owner_id'), 'note_lists', ['owner_id'], unique=False)
    op.create_index(op.f('ix_note_lists_parent_list_id'), 'note_lists', ['parent_list_id'], unique=False)
    
    # 3. Add note_list_id to notes and change constraint
    op.add_column('notes', sa.Column('note_list_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_notes_note_list_id'), 'notes', ['note_list_id'], unique=False)
    op.create_foreign_key(
        'fk_notes_note_list_id_note_lists', 'notes', 'note_lists',
        ['note_list_id'], ['id'], ondelete='CASCADE'
    )
    
    # 4. Create new association tables
    # task_notes (tasks can contain notes)
    op.create_table(
        'task_notes',
        sa.Column('task_id', sa.UUID(), nullable=False),
        sa.Column('note_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['note_id'], ['notes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('task_id', 'note_id')
    )
    
    # tag_notes (tags can contain notes)
    op.create_table(
        'tag_notes',
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.Column('note_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['note_id'], ['notes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tag_id', 'note_id')
    )
    
    # note_list_tags (note lists can be tagged)
    op.create_table(
        'note_list_tags',
        sa.Column('note_list_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['note_list_id'], ['note_lists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('note_list_id', 'tag_id')
    )
    
    # tag_list_tags (tag lists can be tagged)
    op.create_table(
        'tag_list_tags',
        sa.Column('tag_list_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['tag_list_id'], ['tag_lists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tag_list_id', 'tag_id')
    )
    
    # 5. Data migration: Move existing notes to note_lists
    # This is a placeholder - in a real migration you'd need to:
    # - Create default note lists for each user
    # - Update notes to reference those note lists
    # - Then remove the old task_id column and constraint
    # For now, we'll leave both columns and let the application handle the transition


def downgrade() -> None:
    # Reverse all the changes in reverse order
    
    # Drop new association tables
    op.drop_table('tag_list_tags')
    op.drop_table('note_list_tags')
    op.drop_table('tag_notes')
    op.drop_table('task_notes')
    
    # Drop note_list_id from notes
    op.drop_constraint('fk_notes_note_list_id_note_lists', 'notes', type_='foreignkey')
    op.drop_index(op.f('ix_notes_note_list_id'), table_name='notes')
    op.drop_column('notes', 'note_list_id')
    
    # Drop note_lists table
    op.drop_index(op.f('ix_note_lists_parent_list_id'), table_name='note_lists')
    op.drop_index(op.f('ix_note_lists_owner_id'), table_name='note_lists')
    op.drop_table('note_lists')
    
    # Remove hierarchy from tags
    op.drop_constraint('fk_tags_parent_id_tags', 'tags', type_='foreignkey')
    op.drop_index(op.f('ix_tags_parent_id'), table_name='tags')
    op.drop_column('tags', 'parent_id')
    
    # Remove hierarchy from tag_lists
    op.drop_constraint('fk_tag_lists_parent_list_id_tag_lists', 'tag_lists', type_='foreignkey')
    op.drop_index(op.f('ix_tag_lists_parent_list_id'), table_name='tag_lists')
    op.drop_column('tag_lists', 'parent_list_id')
    
    # Remove hierarchy from task_lists
    op.drop_constraint('fk_task_lists_parent_list_id_task_lists', 'task_lists', type_='foreignkey')
    op.drop_index(op.f('ix_task_lists_parent_list_id'), table_name='task_lists')
    op.drop_column('task_lists', 'parent_list_id')

