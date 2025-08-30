import uuid
from sqlalchemy import String, Text, DateTime, func, ForeignKey, CheckConstraint, Enum, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from .enums import ArtifactKind


class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        CheckConstraint(
            "(task_id IS NOT NULL AND list_id IS NULL) OR (task_id IS NULL AND list_id IS NOT NULL)",
            name="ck_artifact_exactly_one_parent",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    list_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("task_lists.id", ondelete="CASCADE"), nullable=True, index=True)
    kind: Mapped[ArtifactKind] = mapped_column(Enum(ArtifactKind, name="artifact_kind", native_enum=True), nullable=False)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    task = relationship("Task", back_populates="artifacts")
    list = relationship("TaskList", back_populates="artifacts")

