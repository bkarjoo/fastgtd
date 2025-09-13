import uuid
from datetime import datetime
from pydantic import BaseModel


class ArtifactBase(BaseModel):
    original_filename: str
    mime_type: str | None = None


class ArtifactCreate(ArtifactBase):
    node_id: uuid.UUID


class ArtifactResponse(ArtifactBase):
    id: uuid.UUID
    node_id: uuid.UUID
    filename: str
    size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True


class ArtifactList(BaseModel):
    artifacts: list[ArtifactResponse]
    total: int