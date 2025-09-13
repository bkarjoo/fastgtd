import os
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.auth import get_current_user
from app.core.config import get_settings
from app.db.deps import get_db
from app.models.artifact import Artifact
from app.models.node import Node
from app.models.user import User
from app.schemas.artifact import ArtifactResponse, ArtifactList

router = APIRouter()


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def upload_artifact(
    node_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file and attach it to a node."""
    settings = get_settings()
    
    # Verify node exists and belongs to user
    result = await db.execute(select(Node).filter(Node.id == node_id, Node.owner_id == current_user.id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Create storage directory if it doesn't exist
    storage_path = Path(settings.file_storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_uuid = uuid.uuid4()
    file_extension = Path(file.filename or "").suffix
    unique_filename = f"{file_uuid}{file_extension}"
    file_path = storage_path / unique_filename
    
    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create artifact record
        artifact = Artifact(
            node_id=node_id,
            filename=unique_filename,
            original_filename=file.filename or "unknown",
            file_path=str(file_path),
            mime_type=file.content_type,
            size_bytes=len(content)
        )
        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)
        
        return artifact
        
    except Exception as e:
        # Clean up file if database operation fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download an artifact file."""
    # Get artifact and verify user access through node ownership
    result = await db.execute(
        select(Artifact)
        .join(Node)
        .filter(
            Artifact.id == artifact_id,
            Node.owner_id == current_user.id
        )
    )
    artifact = result.scalar_one_or_none()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    file_path = Path(artifact.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=artifact.original_filename,
        media_type=artifact.mime_type
    )


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an artifact and its file."""
    # Get artifact and verify user access through node ownership
    result = await db.execute(
        select(Artifact)
        .join(Node)
        .filter(
            Artifact.id == artifact_id,
            Node.owner_id == current_user.id
        )
    )
    artifact = result.scalar_one_or_none()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Delete file from disk
    file_path = Path(artifact.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass  # File might already be deleted, continue with database cleanup
    
    # Delete artifact record
    await db.delete(artifact)
    await db.commit()


@router.get("/node/{node_id}", response_model=ArtifactList)
async def get_node_artifacts(
    node_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all artifacts for a node."""
    # Verify node exists and belongs to user
    result = await db.execute(select(Node).filter(Node.id == node_id, Node.owner_id == current_user.id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    artifacts_result = await db.execute(select(Artifact).filter(Artifact.node_id == node_id))
    artifacts = artifacts_result.scalars().all()
    
    return ArtifactList(
        artifacts=list(artifacts),
        total=len(artifacts)
    )