import uuid
from sqlalchemy import DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DefaultNode(Base):
    """Stores the default node for each user - one row per user"""
    __tablename__ = "default_nodes"

    # One row per user  
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("nodes.id", ondelete="CASCADE"), 
        nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationships
    owner = relationship("User", back_populates="default_node", foreign_keys=[owner_id])
    node = relationship("Node")

    def __repr__(self):
        return f"<DefaultNode(owner_id={self.owner_id}, node_id={self.node_id})>"