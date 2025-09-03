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
    JSON,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from .enums import TaskPriority, TaskStatus


class Node(Base):
    """Base node class for polymorphic inheritance"""
    __tablename__ = "nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=True, index=True)
    node_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="nodes")
    parent = relationship("Node", remote_side="Node.id", back_populates="children")
    children = relationship("Node", back_populates="parent", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="node_tags", back_populates="nodes")

    # Polymorphic configuration
    __mapper_args__ = {
        "polymorphic_on": node_type,
        "polymorphic_identity": "node"
    }

    @property
    def is_list(self) -> bool:
        """A node becomes a list when it has children"""
        return len(self.children) > 0

    def __repr__(self):
        return f"<Node(id={self.id}, type={self.node_type}, title='{self.title}')>"


class Task(Node):
    """Task node - inherits from Node"""
    __tablename__ = "node_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("nodes.id"), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, name="task_status", native_enum=True), nullable=False, default=TaskStatus.todo)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority, name="task_priority", native_enum=True), nullable=False, default=TaskPriority.medium)
    due_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    earliest_start_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recurrence_rule: Mapped[str | None] = mapped_column(Text, nullable=True)
    recurrence_anchor: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __mapper_args__ = {"polymorphic_identity": "task"}

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status={self.status})>"


class Note(Node):
    """Note node - inherits from Node"""
    __tablename__ = "node_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("nodes.id"), primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "note"}

    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}')>"


class SmartFolder(Node):
    """Smart folder node - subscribes to a single rule for filtering"""
    __tablename__ = "node_smart_folders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("nodes.id"), primary_key=True)
    
    # Reference to the rule this smart folder uses
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("rules.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # Legacy column - will be removed after migration
    rules: Mapped[dict | None] = mapped_column(
        JSON, 
        nullable=True, 
        default=lambda: {"conditions": [], "logic": "AND"},
        comment="DEPRECATED - Use rule_id instead"
    )
    
    auto_refresh: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationship to Rule
    rule = relationship("Rule", back_populates="smart_folders")

    __mapper_args__ = {"polymorphic_identity": "smart_folder"}

    def __repr__(self):
        return f"<SmartFolder(id={self.id}, title='{self.title}', rule_id={self.rule_id})>"


class Template(Node):
    """Template node - blueprint for creating structured content hierarchies"""
    __tablename__ = "node_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("nodes.id"), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("nodes.id", ondelete="SET NULL"), 
        nullable=True
    )
    create_container: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __mapper_args__ = {
        "polymorphic_identity": "template",
        "inherit_condition": text("node_templates.id = nodes.id")
    }

    def __repr__(self):
        return f"<Template(id={self.id}, title='{self.title}', category='{self.category}', target_node_id={self.target_node_id}, create_container={self.create_container})>"


class Folder(Node):
    """Folder node - pure organizational container
    
    Folders don't have any additional fields beyond the base Node.
    They exist purely for organization and hierarchy.
    """
    __mapper_args__ = {"polymorphic_identity": "folder"}
    
    def __repr__(self):
        return f"<Folder(id={self.id}, title='{self.title}')>"


# Useful indexes
Index("ix_node_owner_sort", Node.owner_id, Node.sort_order)
Index("ix_node_parent", Node.parent_id)
Index("ix_node_type", Node.node_type)
Index("ix_task_status", Task.status)
Index("ix_task_priority", Task.priority)
Index("ix_task_due_at", Task.due_at)