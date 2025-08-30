"""migrate_notes_to_note_lists

Revision ID: f4c37a12c90c
Revises: f67fef330ae9
Create Date: 2025-08-14 19:48:22.503650

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4c37a12c90c'
down_revision: Union[str, None] = 'f67fef330ae9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This migration handles the data transition from task-based notes to note-list-based notes
    
    connection = op.get_bind()
    
    # 1. Create default note lists for each user
    connection.execute(sa.text("""
        INSERT INTO note_lists (id, owner_id, name, description, sort_order, created_at, updated_at)
        SELECT 
            gen_random_uuid(),
            u.id,
            'Default Notes',
            'Auto-created during migration',
            0,
            NOW(),
            NOW()
        FROM users u
        WHERE NOT EXISTS (
            SELECT 1 FROM note_lists nl WHERE nl.owner_id = u.id
        )
    """))
    
    # 2. Migrate notes with valid task references to appropriate note lists
    connection.execute(sa.text("""
        UPDATE notes 
        SET note_list_id = (
            SELECT nl.id 
            FROM note_lists nl
            JOIN users u ON nl.owner_id = u.id
            JOIN task_lists tl ON tl.owner_id = u.id
            JOIN tasks t ON t.list_id = tl.id
            WHERE t.id = notes.task_id
            AND nl.name = 'Default Notes'
            LIMIT 1
        )
        WHERE note_list_id IS NULL 
        AND task_id IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM tasks t 
            JOIN task_lists tl ON t.list_id = tl.id
            WHERE t.id = notes.task_id
        )
    """))
    
    # 3. Handle orphaned notes by finding the note owner through task ownership
    connection.execute(sa.text("""
        UPDATE notes 
        SET note_list_id = (
            SELECT nl.id 
            FROM note_lists nl
            WHERE nl.owner_id = (
                SELECT tl.owner_id 
                FROM tasks t 
                JOIN task_lists tl ON t.list_id = tl.id
                WHERE t.id = notes.task_id
                LIMIT 1
            )
            AND nl.name = 'Default Notes'
            LIMIT 1
        )
        WHERE note_list_id IS NULL 
        AND task_id IS NOT NULL
    """))
    
    # 4. Handle any remaining orphaned notes - assign to first available user's default list
    connection.execute(sa.text("""
        UPDATE notes 
        SET note_list_id = (
            SELECT id FROM note_lists WHERE name = 'Default Notes' LIMIT 1
        )
        WHERE note_list_id IS NULL
    """))
    
    # 5. Verify all notes have been assigned
    result = connection.execute(sa.text("SELECT COUNT(*) FROM notes WHERE note_list_id IS NULL"))
    unassigned_count = result.scalar()
    if unassigned_count > 0:
        raise Exception(f"Migration failed: {unassigned_count} notes still unassigned")
    
    # 6. Make note_list_id required
    op.alter_column('notes', 'note_list_id', nullable=False)
    
    # 7. Check if old constraint exists and drop it
    constraint_exists = connection.execute(sa.text("""
        SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE table_name = 'notes' 
        AND constraint_name = 'ck_note_requires_task'
        AND table_schema = current_schema()
    """)).scalar()
    
    if constraint_exists > 0:
        op.drop_constraint('ck_note_requires_task', 'notes', type_='check')
    
    # 8. Add new constraint
    op.create_check_constraint(
        'ck_note_requires_note_list',
        'notes',
        'note_list_id IS NOT NULL'
    )


def downgrade() -> None:
    # This downgrade attempts to restore notes back to task-based structure
    # WARNING: This is potentially destructive and may result in data loss
    
    connection = op.get_bind()
    
    # 1. Check if new constraint exists and drop it
    constraint_exists = connection.execute(sa.text("""
        SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE table_name = 'notes' 
        AND constraint_name = 'ck_note_requires_note_list'
        AND table_schema = current_schema()
    """)).scalar()
    
    if constraint_exists > 0:
        op.drop_constraint('ck_note_requires_note_list', 'notes', type_='check')
    
    # 2. Make note_list_id nullable
    op.alter_column('notes', 'note_list_id', nullable=True)
    
    # 3. Attempt to restore task associations for notes that were migrated
    # This tries to find a valid task for each note based on ownership
    connection.execute(sa.text("""
        UPDATE notes 
        SET task_id = (
            SELECT t.id 
            FROM tasks t
            JOIN task_lists tl ON t.list_id = tl.id
            JOIN note_lists nl ON tl.owner_id = nl.owner_id
            WHERE nl.id = notes.note_list_id
            AND notes.task_id IS NULL
            LIMIT 1
        )
        WHERE task_id IS NULL
        AND note_list_id IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM tasks t
            JOIN task_lists tl ON t.list_id = tl.id
            JOIN note_lists nl ON tl.owner_id = nl.owner_id
            WHERE nl.id = notes.note_list_id
        )
    """))
    
    # 4. For notes that can't be reassigned to tasks, keep them as orphaned
    # Log how many notes couldn't be restored
    orphaned_count = connection.execute(sa.text("""
        SELECT COUNT(*) FROM notes 
        WHERE task_id IS NULL AND note_list_id IS NOT NULL
    """)).scalar()
    
    if orphaned_count > 0:
        print(f"WARNING: {orphaned_count} notes could not be restored to task associations")
        print("These notes will remain associated with note_lists only")
    
    # 5. Restore old constraint if we're going back to task-only model
    old_constraint_exists = connection.execute(sa.text("""
        SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE table_name = 'notes' 
        AND constraint_name = 'ck_note_requires_task'
        AND table_schema = current_schema()
    """)).scalar()
    
    if old_constraint_exists == 0:
        # Only recreate if all notes have valid task_id
        notes_without_tasks = connection.execute(sa.text("""
            SELECT COUNT(*) FROM notes WHERE task_id IS NULL
        """)).scalar()
        
        if notes_without_tasks == 0:
            op.create_check_constraint(
                'ck_note_requires_task',
                'notes', 
                'task_id IS NOT NULL'
            )
        else:
            print(f"WARNING: Cannot restore task constraint - {notes_without_tasks} notes have no task association")
    
    # Note: We intentionally don't delete note_lists table to prevent data loss
    # The note_list_id column remains for potential future re-migration

