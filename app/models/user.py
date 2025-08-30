import uuid
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # New unified relationships
    nodes = relationship("Node", back_populates="owner", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="owner", cascade="all, delete-orphan")
    default_node = relationship("DefaultNode", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Legacy relationships - disabled during migration
    # lists = relationship("TaskList", back_populates="owner", cascade="all, delete-orphan")
    # tag_lists = relationship("TagList", back_populates="owner", cascade="all, delete-orphan")
    # note_lists = relationship("NoteList", back_populates="owner", cascade="all, delete-orphan")
