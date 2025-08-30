import uuid
from datetime import datetime
from pydantic import BaseModel

from app.models.enums import ArtifactKind


class ArtifactCreate(BaseModel):
    kind: ArtifactKind
    uri: str
    title: str | None = None
    description: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    task_id: uuid.UUID | None = None
    list_id: uuid.UUID | None = None


class ArtifactUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    uri: str | None = None
    kind: ArtifactKind | None = None


class ArtifactOut(BaseModel):
    id: uuid.UUID
    kind: ArtifactKind
    uri: str
    title: str | None
    description: str | None
    mime_type: str | None
    size_bytes: int | None
    task_id: uuid.UUID | None
    list_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
