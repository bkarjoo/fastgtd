"""add note_list_taglists and task_list_taglists; enforce non-null tag.tag_list_id

Revision ID: ab12cd34ef56
Revises: e7f8a9b0c1d2
Create Date: 2025-08-16 07:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = 'ab12cd34ef56'
down_revision: Union[str, None] = 'e7f8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # M2M for note lists -> tag lists
    op.create_table(
        'note_list_taglists',
        sa.Column('note_list_id', sa.UUID(), nullable=False),
        sa.Column('tag_list_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['note_list_id'], ['note_lists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_list_id'], ['tag_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('note_list_id', 'tag_list_id')
    )

    # M2M for task lists -> tag lists
    op.create_table(
        'task_list_taglists',
        sa.Column('task_list_id', sa.UUID(), nullable=False),
        sa.Column('tag_list_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['task_list_id'], ['task_lists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_list_id'], ['tag_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('task_list_id', 'tag_list_id')
    )

    # Enforce non-null tag_list_id and restrict deletes
    # 1) Backfill NULL tag_list_id using per-user default TagList "All Tags"
    conn = op.get_bind()
    # find owners with NULL tag_list_id
    owners = conn.execute(sa.text("SELECT DISTINCT owner_id FROM tags WHERE tag_list_id IS NULL")).fetchall()
    for (owner_id,) in owners:
        # get or create 'All Tags' tag_list for this owner
        row = conn.execute(
            sa.text("SELECT id FROM tag_lists WHERE owner_id=:owner_id AND name=:name"),
            {"owner_id": owner_id, "name": "All Tags"},
        ).fetchone()
        if row is None:
            tl_id = str(uuid.uuid4())
            conn.execute(
                sa.text(
                    "INSERT INTO tag_lists (id, owner_id, name, description, sort_order) VALUES (:id, :owner_id, :name, NULL, 0)"
                ),
                {"id": tl_id, "owner_id": owner_id, "name": "All Tags"},
            )
        else:
            tl_id = row[0]
        # update tags for this owner to point to the default tag_list
        conn.execute(
            sa.text(
                "UPDATE tags SET tag_list_id=:tl_id WHERE owner_id=:owner_id AND tag_list_id IS NULL"
            ),
            {"tl_id": tl_id, "owner_id": owner_id},
        )

    # 2) Drop old FK if it exists
    try:
        op.drop_constraint('fk_tags_tag_list_id_tag_lists', 'tags', type_='foreignkey')
    except Exception:
        pass
    # 3) Make column non-nullable
    op.alter_column('tags', 'tag_list_id', existing_type=sa.UUID(), nullable=False)
    # 4) Recreate FK with RESTRICT
    op.create_foreign_key(
        'fk_tags_tag_list_id_tag_lists', 'tags', 'tag_lists', ['tag_list_id'], ['id'], ondelete='RESTRICT'
    )


def downgrade() -> None:
    # Revert tag FK to nullable SET NULL
    try:
        op.drop_constraint('fk_tags_tag_list_id_tag_lists', 'tags', type_='foreignkey')
    except Exception:
        pass
    op.alter_column('tags', 'tag_list_id', existing_type=sa.UUID(), nullable=True)
    op.create_foreign_key(
        'fk_tags_tag_list_id_tag_lists', 'tags', 'tag_lists', ['tag_list_id'], ['id'], ondelete='SET NULL'
    )

    op.drop_table('task_list_taglists')
    op.drop_table('note_list_taglists')
