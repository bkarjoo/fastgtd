import uuid
from datetime import datetime
from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None
    tag_list_id: uuid.UUID
    sort_order: int | None = None


class TagUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    tag_list_id: uuid.UUID | None = None
    sort_order: int | None = None


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
