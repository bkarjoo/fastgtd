import uuid
from sqlalchemy import String, Text, Integer, DateTime, func, ForeignKey, UniqueConstraint, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.associations import tag_list_tags


class TagList(Base):
    __tablename__ = "tag_lists"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_taglist_owner_name"),
        CheckConstraint(
            "(is_system_root AND parent_list_id IS NULL) OR (NOT is_system_root AND parent_list_id IS NOT NULL)",
            name="ck_taglist_parent_null_only_for_root",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    parent_list_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tag_lists.id", ondelete="CASCADE"), nullable=True, index=True)
    is_system_root: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Legacy relationships - disabled during unified migration
    # owner = relationship("User", back_populates="tag_lists")
    # parent = relationship("TagList", remote_side="TagList.id", back_populates="children")
    # children = relationship("TagList", back_populates="parent", cascade="all, delete-orphan")
    # tags = relationship("Tag", back_populates="tag_list")
    # tag_relationships = relationship("Tag", secondary=tag_list_tags, back_populates="tag_lists")
