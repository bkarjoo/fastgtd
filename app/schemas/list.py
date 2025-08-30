import uuid
from datetime import datetime
from pydantic import BaseModel


class TaskListCreate(BaseModel):
    name: str
    description: str | None = None
    sort_order: int | None = 0


class TaskListUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None


class TaskListParentUpdate(BaseModel):
    parent_list_id: uuid.UUID | None = None


class TaskListOut(BaseModel):
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

