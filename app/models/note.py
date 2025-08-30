import uuid
from sqlalchemy import String, Text, DateTime, func, ForeignKey, CheckConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.associations import tag_notes, note_links, note_tasks, tag_notes as tag_notes_assoc, task_notes


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = (
        CheckConstraint(
            "note_list_id IS NOT NULL",
            name="ck_note_requires_note_list",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_list_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("note_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    note_list = relationship("NoteList", back_populates="notes")
    parent = relationship("Note", remote_side="Note.id", back_populates="children")
    children = relationship("Note", back_populates="parent", cascade="all, delete-orphan")
    
    tags = relationship("Tag", secondary=tag_notes, back_populates="notes")
    contained_tasks = relationship("Task", secondary=note_tasks, back_populates="containing_notes")
    containing_tasks = relationship("Task", secondary=task_notes, back_populates="contained_notes")
    containing_tags = relationship("Tag", secondary=tag_notes, back_populates="contained_notes")
    
    linked_to = relationship(
        "Note",
        secondary=note_links,
        primaryjoin="Note.id == note_links.c.source_note_id",
        secondaryjoin="Note.id == note_links.c.target_note_id",
        back_populates="linked_from"
    )
    linked_from = relationship(
        "Note",
        secondary=note_links,
        primaryjoin="Note.id == note_links.c.target_note_id",
        secondaryjoin="Note.id == note_links.c.source_note_id",
        back_populates="linked_to"
    )
