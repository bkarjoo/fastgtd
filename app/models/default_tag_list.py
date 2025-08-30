import uuid
from sqlalchemy import DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DefaultTagList(Base):
  __tablename__ = "default_tag_lists"

  user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
  tag_list_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tag_lists.id", ondelete="CASCADE"), nullable=False)
  created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

