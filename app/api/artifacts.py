import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.deps import get_db
from app.models.artifact import Artifact
from app.models.task import Task
from app.models.task_list import TaskList
from app.models.user import User
from app.schemas.artifact import ArtifactCreate, ArtifactUpdate, ArtifactOut


router = APIRouter(prefix="/artifacts", tags=["artifacts"])


async def _ensure_owned_list(db: AsyncSession, owner_id: uuid.UUID, list_id: uuid.UUID) -> TaskList:
    res = await db.execute(select(TaskList).where(TaskList.id == list_id, TaskList.owner_id == owner_id))
    lst = res.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="list_not_found")
    return lst


async def _ensure_owned_task(db: AsyncSession, owner_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    res = await db.execute(select(Task).join(TaskList).where(Task.id == task_id, TaskList.owner_id == owner_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task_not_found")
    return task


@router.post("", response_model=ArtifactOut, status_code=201)
async def create_artifact(
    payload: ArtifactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if (payload.task_id is None) == (payload.list_id is None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="provide exactly one of task_id or list_id")
    if payload.task_id:
        await _ensure_owned_task(db, current_user.id, payload.task_id)
    if payload.list_id:
        await _ensure_owned_list(db, current_user.id, payload.list_id)

    art = Artifact(
        kind=payload.kind,
        uri=payload.uri,
        title=payload.title,
        description=payload.description,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        task_id=payload.task_id,
        list_id=payload.list_id,
    )
    db.add(art)
    await db.commit()
    await db.refresh(art)
    return art


@router.get("", response_model=list[ArtifactOut])
async def list_artifacts(
    task_id: uuid.UUID | None = None,
    list_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if (task_id is None) == (list_id is None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="provide exactly one of task_id or list_id")
    if task_id is not None:
        await _ensure_owned_task(db, current_user.id, task_id)
        res = await db.execute(
            select(Artifact).where(Artifact.task_id == task_id).order_by(Artifact.created_at).limit(limit).offset(offset)
        )
        return res.scalars().all()
    else:
        assert list_id is not None
        await _ensure_owned_list(db, current_user.id, list_id)
        res = await db.execute(
            select(Artifact).where(Artifact.list_id == list_id).order_by(Artifact.created_at).limit(limit).offset(offset)
        )
        return res.scalars().all()


async def _get_owned_artifact_or_404(db: AsyncSession, owner_id: uuid.UUID, artifact_id: uuid.UUID) -> Artifact:
    res = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
    art = res.scalar_one_or_none()
    if not art:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="artifact_not_found")
    if art.task_id:
        await _ensure_owned_task(db, owner_id, art.task_id)
    elif art.list_id:
        await _ensure_owned_list(db, owner_id, art.list_id)
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="artifact_parent_missing")
    return art


@router.get("/{artifact_id}", response_model=ArtifactOut)
async def get_artifact(
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_owned_artifact_or_404(db, current_user.id, artifact_id)


@router.patch("/{artifact_id}", response_model=ArtifactOut)
async def update_artifact(
    artifact_id: uuid.UUID,
    payload: ArtifactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    art = await _get_owned_artifact_or_404(db, current_user.id, artifact_id)
    if payload.title is not None:
        art.title = payload.title
    if payload.description is not None:
        art.description = payload.description
    if payload.mime_type is not None:
        art.mime_type = payload.mime_type
    if payload.size_bytes is not None:
        art.size_bytes = payload.size_bytes
    if payload.uri is not None:
        art.uri = payload.uri
    if payload.kind is not None:
        art.kind = payload.kind
    await db.commit()
    await db.refresh(art)
    return art


@router.delete("/{artifact_id}", status_code=204)
async def delete_artifact(
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    art = await _get_owned_artifact_or_404(db, current_user.id, artifact_id)
    await db.delete(art)
    await db.commit()
    return None
