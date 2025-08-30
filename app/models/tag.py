import uuid
from sqlalchemy import String, Text, DateTime, func, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.node_associations import node_tags


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_tag_owner_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex color code
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Unified node system relationships
    owner = relationship("User", back_populates="tags")
    nodes = relationship("Node", secondary=node_tags, back_populates="tags")
