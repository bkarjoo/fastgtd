"""cleanup_notes_constraints

Revision ID: e7f8a9b0c1d2
Revises: d1e2f3a4b5c6
Create Date: 2025-08-16 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    # Drop legacy check constraint if exists
    exists = conn.execute(sa.text("""
        SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE table_name = 'notes' 
          AND constraint_type = 'CHECK'
          AND constraint_name = 'ck_note_exactly_one_parent'
          AND table_schema = current_schema()
    """)).scalar()
    if exists and int(exists) > 0:
        op.drop_constraint('ck_note_exactly_one_parent', 'notes', type_='check')
    # Drop legacy columns and indexes if present
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('notes')]
    idxs = {i['name'] for i in inspector.get_indexes('notes')}
    if 'list_id' in cols:
        if 'ix_notes_list_id' in idxs:
            op.drop_index('ix_notes_list_id', table_name='notes')
        op.drop_column('notes', 'list_id')
    if 'task_id' in cols:
        if 'ix_notes_task_id' in idxs:
            op.drop_index('ix_notes_task_id', table_name='notes')
        op.drop_column('notes', 'task_id')


def downgrade() -> None:
    # Downgrade: re-add legacy columns without data backfill
    op.add_column('notes', sa.Column('list_id', sa.UUID(), nullable=True))
    op.add_column('notes', sa.Column('task_id', sa.UUID(), nullable=True))
    op.create_index('ix_notes_list_id', 'notes', ['list_id'], unique=False)
    op.create_index('ix_notes_task_id', 'notes', ['task_id'], unique=False)
    # Recreate old check constraint
    op.create_check_constraint('ck_note_exactly_one_parent', 'notes', '(task_id IS NOT NULL AND note_list_id IS NULL) OR (task_id IS NULL AND note_list_id IS NOT NULL)')
