"""
Rule model - Standalone, composable filtering rules
"""
import uuid
from sqlalchemy import (
    String,
    Text,
    DateTime,
    func,
    ForeignKey,
    JSON,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Rule(Base):
    """
    Standalone rule entity that can be composed and reused.
    Rules can reference other rules for composition.
    Smart folders subscribe to a single rule.
    """
    __tablename__ = "rules"

    # Core fields
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="Human-readable name for the rule"
    )
    
    description: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True,
        comment="Optional description of what this rule filters"
    )
    
    # Rule definition
    rule_data: Mapped[dict] = mapped_column(
        JSON, 
        nullable=False, 
        default=lambda: {"conditions": [], "logic": "AND"},
        comment="JSON structure containing conditions and logic"
    )
    
    # Metadata
    is_public: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="Whether this rule can be used by other users"
    )
    
    is_system: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="System-provided rules that cannot be edited"
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
    owner = relationship("User", back_populates="rules")
    smart_folders = relationship("SmartFolder", back_populates="rule")
    
    def to_dict(self):
        """Convert rule to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "rule_data": self.rule_data,
            "is_public": self.is_public,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Rule(id={self.id}, name='{self.name}')>"