import uuid
from datetime import datetime
from pydantic import BaseModel

from app.models.enums import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    list_id: uuid.UUID
    title: str
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_at: datetime | None = None
    earliest_start_at: datetime | None = None
    parent_id: uuid.UUID | None = None
    sort_order: int | None = 0
    # RFC 5545 RRULE string (e.g., "FREQ=DAILY;INTERVAL=1")
    recurrence_rule: str | None = None
    # Anchor for recurrence expansion (defaults to due_at if omitted)
    recurrence_anchor: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_at: datetime | None = None
    earliest_start_at: datetime | None = None
    completed_at: datetime | None = None
    archived: bool | None = None
    parent_id: uuid.UUID | None = None
    sort_order: int | None = None
    list_id: uuid.UUID | None = None
    recurrence_rule: str | None = None
    recurrence_anchor: datetime | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    list_id: uuid.UUID
    parent_id: uuid.UUID | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_at: datetime | None
    earliest_start_at: datetime | None
    completed_at: datetime | None
    archived: bool
    sort_order: int
    recurrence_rule: str | None
    recurrence_anchor: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
