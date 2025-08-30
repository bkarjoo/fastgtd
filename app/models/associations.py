import uuid
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

list_tags = Table(
    "list_tags",
    Base.metadata,
    Column("list_id", UUID(as_uuid=True), ForeignKey("task_lists.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

note_links = Table(
    "note_links",
    Base.metadata,
    Column("source_note_id", UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("target_note_id", UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
)

note_tasks = Table(
    "note_tasks",
    Base.metadata,
    Column("note_id", UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("task_id", UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
)

tag_notes = Table(
    "tag_notes",
    Base.metadata,
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Column("note_id", UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
)

note_list_tags = Table(
    "note_list_tags",
    Base.metadata,
    Column("note_list_id", UUID(as_uuid=True), ForeignKey("note_lists.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

task_notes = Table(
    "task_notes",
    Base.metadata,
    Column("task_id", UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("note_id", UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
)

tag_list_tags = Table(
    "tag_list_tags",
    Base.metadata,
    Column("tag_list_id", UUID(as_uuid=True), ForeignKey("tag_lists.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

# New: Multi-TagList associations for NoteList and TaskList (used for allowed tags inheritance)
note_list_taglists = Table(
    "note_list_taglists",
    Base.metadata,
    Column("note_list_id", UUID(as_uuid=True), ForeignKey("note_lists.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_list_id", UUID(as_uuid=True), ForeignKey("tag_lists.id", ondelete="CASCADE"), primary_key=True),
)

task_list_taglists = Table(
    "task_list_taglists",
    Base.metadata,
    Column("task_list_id", UUID(as_uuid=True), ForeignKey("task_lists.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_list_id", UUID(as_uuid=True), ForeignKey("tag_lists.id", ondelete="CASCADE"), primary_key=True),
)
