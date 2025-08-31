"""Pydantic schemas for Rules."""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class RuleBase(BaseModel):
    """Base schema for Rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rule_data: Dict[str, Any] = Field(
        default_factory=lambda: {"conditions": [], "logic": "AND"}
    )
    is_public: bool = False


class RuleCreate(RuleBase):
    """Schema for creating a Rule."""
    pass


class RuleUpdate(BaseModel):
    """Schema for updating a Rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rule_data: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class RuleResponse(RuleBase):
    """Schema for Rule response."""
    id: UUID
    owner_id: UUID
    is_system: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


class RuleListResponse(BaseModel):
    """Schema for list of Rules response."""
    rules: List[RuleResponse]
    total: int