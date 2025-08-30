import uuid
from datetime import datetime
from pydantic import BaseModel


class TagListCreate(BaseModel):
    name: str
    description: str | None = None
    sort_order: int | None = 0


class TagListUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None


class TagListParentUpdate(BaseModel):
    parent_list_id: uuid.UUID | None = None


class TagListOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    parent_list_id: uuid.UUID | None
    name: str
    description: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

