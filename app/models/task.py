import uuid
from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    func,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from .enums import TaskPriority, TaskStatus


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("task_lists.id", ondelete="CASCADE"), index=True, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, name="task_status", native_enum=True), nullable=False, default=TaskStatus.todo)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority, name="task_priority", native_enum=True), nullable=False, default=TaskPriority.medium)
    due_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Do not consider task before this timestamp (postponement)
    earliest_start_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Recurrence support (RFC 5545 RRULE stored as text)
    # Example: "FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,WE,FR"
    recurrence_rule: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Anchor date for recurrence expansion (defaults to due_at if not provided)
    recurrence_anchor: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    list = relationship("TaskList", back_populates="tasks")
    parent = relationship("Task", remote_side="Task.id", back_populates="children")
    children = relationship("Task", back_populates="parent", cascade="all, delete-orphan")

    tags = relationship("Tag", secondary="task_tags", back_populates="tasks")
    contained_notes = relationship("Note", secondary="task_notes", back_populates="containing_tasks")
    containing_notes = relationship("Note", secondary="task_notes", back_populates="contained_tasks")
    artifacts = relationship("Artifact", back_populates="task", cascade="all, delete-orphan")


# Useful indexes
Index("ix_task_list_sort", Task.list_id, Task.sort_order)
Index("ix_task_status", Task.status)
Index("ix_task_priority", Task.priority)
Index("ix_task_due_at", Task.due_at)
