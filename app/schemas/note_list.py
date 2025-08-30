import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NoteListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sort_order: Optional[int] = 0


class NoteListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class NoteListParentUpdate(BaseModel):
    parent_list_id: Optional[uuid.UUID] = None


class NoteListOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    parent_list_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True