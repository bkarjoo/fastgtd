"""add_note_parent_and_title

Revision ID: d1e2f3a4b5c6
Revises: f4c37a12c90c
Create Date: 2025-08-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'f4c37a12c90c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add parent_id and title to notes if not present
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('notes')]

    if 'parent_id' not in cols:
        op.add_column('notes', sa.Column('parent_id', sa.UUID(), nullable=True))
        op.create_index(op.f('ix_notes_parent_id'), 'notes', ['parent_id'], unique=False)
        op.create_foreign_key(
            'fk_notes_parent_id_notes', 'notes', 'notes',
            ['parent_id'], ['id'], ondelete='CASCADE'
        )
    if 'title' not in cols:
        op.add_column('notes', sa.Column('title', sa.String(length=255), nullable=True))
        # Backfill a default title for existing rows
        conn.execute(sa.text("""
            UPDATE notes SET title = COALESCE(title, SUBSTRING(body FROM 1 FOR 80))
        """))
        # Ensure non-null title
        op.alter_column('notes', 'title', existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    # Drop added columns/constraints if they exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('notes')]

    if 'parent_id' in cols:
        op.drop_constraint('fk_notes_parent_id_notes', 'notes', type_='foreignkey')
        op.drop_index(op.f('ix_notes_parent_id'), table_name='notes')
        op.drop_column('notes', 'parent_id')
    if 'title' in cols:
        op.drop_column('notes', 'title')
