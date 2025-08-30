"""add tag_lists and tag.tag_list_id

Revision ID: c3d5e6f7a8b9
Revises: 9c9c2c3d7a1a
Create Date: 2025-08-10 10:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d5e6f7a8b9'
down_revision: Union[str, None] = '9c9c2c3d7a1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tag_lists',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', 'name', name='uq_taglist_owner_name')
    )
    op.create_index(op.f('ix_tag_lists_owner_id'), 'tag_lists', ['owner_id'], unique=False)

    # Add nullable FK column to tags
    op.add_column('tags', sa.Column('tag_list_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_tags_tag_list_id'), 'tags', ['tag_list_id'], unique=False)
    op.create_foreign_key(
        'fk_tags_tag_list_id_tag_lists', 'tags', 'tag_lists', ['tag_list_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop FK/column/index from tags
    op.drop_constraint('fk_tags_tag_list_id_tag_lists', 'tags', type_='foreignkey')
    op.drop_index(op.f('ix_tags_tag_list_id'), table_name='tags')
    op.drop_column('tags', 'tag_list_id')

    # Drop tag_lists
    op.drop_index(op.f('ix_tag_lists_owner_id'), table_name='tag_lists')
    op.drop_table('tag_lists')

