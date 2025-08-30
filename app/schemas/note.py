import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NoteCreate(BaseModel):
    note_list_id: uuid.UUID
    title: str
    body: str
    parent_id: Optional[uuid.UUID] = None
    sort_order: Optional[int] = None


class NoteUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    parent_id: uuid.UUID | None = None
    note_list_id: uuid.UUID | None = None
    sort_order: int | None = None


class NoteOut(BaseModel):
    id: uuid.UUID
    note_list_id: uuid.UUID
    title: str
    body: str
    parent_id: uuid.UUID | None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
