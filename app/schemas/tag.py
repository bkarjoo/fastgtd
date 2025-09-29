import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator
import re


class TagCreate(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None

    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        if v is not None and v != "":
            if not re.match(r'^#[0-9a-fA-F]{6}$', v):
                raise ValueError('Color must be a valid hex code (e.g., #FF0000)')
        return v


class TagUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None

    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        if v is not None and v != "":
            if not re.match(r'^#[0-9a-fA-F]{6}$', v):
                raise ValueError('Color must be a valid hex code (e.g., #FF0000)')
        return v


class TagOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    tag_list_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    name: str
    description: str | None
    color: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagResponse(BaseModel):
    """Simple tag response for node tags"""
    id: uuid.UUID
    name: str
    description: str | None = None
    color: str | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True
