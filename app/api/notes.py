import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.deps import get_db
from app.models.note import Note
from app.models.note_list import NoteList
from app.models.task import Task
from app.models.tag import Tag
from app.models.user import User
from app.models.associations import tag_notes, note_links, note_tasks, task_notes, note_list_taglists
from app.models.tag_list import TagList
from app.models.note_list import NoteList
from app.schemas.note import NoteCreate, NoteUpdate, NoteOut
from app.models.default_note_list import DefaultNoteList


router = APIRouter(prefix="/notes", tags=["notes"])




async def _ensure_owned_note_list(db: AsyncSession, owner_id: uuid.UUID, note_list_id: uuid.UUID) -> NoteList:
    res = await db.execute(select(NoteList).where(NoteList.id == note_list_id, NoteList.owner_id == owner_id))
    note_list = res.scalar_one_or_none()
    if not note_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="note_list_not_found")
    return note_list


async def _ensure_owned_note(db: AsyncSession, owner_id: uuid.UUID, note_id: uuid.UUID) -> Note:
    res = await db.execute(
        select(Note)
        .join(NoteList)
        .where(Note.id == note_id, NoteList.owner_id == owner_id)
    )
    note = res.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="note_not_found")
    return note


@router.post("/default", response_model=NoteOut, status_code=201)
async def create_note_in_default(
    payload: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ignore incoming note_list_id; use default mapping
    res = await db.execute(select(DefaultNoteList.note_list_id).where(DefaultNoteList.user_id == current_user.id))
    nl_id = res.scalar_one_or_none()
    if nl_id is None:
        # fallback to system root
        res2 = await db.execute(select(NoteList.id).where(NoteList.owner_id == current_user.id, NoteList.is_system_root == True))
        nl_id = res2.scalar_one()
    # compute next sort_order
    res3 = await db.execute(select(func.coalesce(func.max(Note.sort_order) + 1, 0)).where(Note.note_list_id == nl_id, Note.parent_id.is_(None)))
    next_order = res3.scalar_one() or 0
    note = Note(
        note_list_id=nl_id,
        title=payload.title,
        body=payload.body or '',
        parent_id=None,
        sort_order=payload.sort_order if payload.sort_order is not None else next_order,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def _validate_parent_note(db: AsyncSession, owner_id: uuid.UUID, parent_id: uuid.UUID, note_list_id: uuid.UUID) -> None:
    parent_note = await _ensure_owned_note(db, owner_id, parent_id)
    if parent_note.note_list_id != note_list_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="parent_note_must_belong_to_same_note_list"
        )


async def _check_circular_reference(db: AsyncSession, note_id: uuid.UUID, parent_id: uuid.UUID) -> None:
    current_parent_id = parent_id
    visited = {note_id}
    
    while current_parent_id:
        if current_parent_id in visited:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="circular_reference_detected"
            )
        visited.add(current_parent_id)
        
        res = await db.execute(select(Note.parent_id).where(Note.id == current_parent_id))
        current_parent_id = res.scalar_one_or_none()


@router.post("", response_model=NoteOut, status_code=201)
async def create_note(
    payload: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_owned_note_list(db, current_user.id, payload.note_list_id)
    
    if payload.parent_id:
        await _validate_parent_note(db, current_user.id, payload.parent_id, payload.note_list_id)

    # compute next sort_order at end of siblings
    sibling_parent_id = payload.parent_id
    res = await db.execute(
        select(func.coalesce(func.max(Note.sort_order) + 1, 0)).where(
            Note.note_list_id == payload.note_list_id,
            Note.parent_id.is_(sibling_parent_id) if sibling_parent_id is None else Note.parent_id == sibling_parent_id,
        )
    )
    next_order = res.scalar_one() or 0
    note = Note(
        note_list_id=payload.note_list_id,
        title=payload.title,
        body=payload.body,
        parent_id=payload.parent_id,
        sort_order=payload.sort_order if payload.sort_order is not None else next_order,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("", response_model=list[NoteOut])
async def list_notes(
    note_list_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_owned_note_list(db, current_user.id, note_list_id)
    res = await db.execute(
        select(Note).where(Note.note_list_id == note_list_id).order_by(Note.created_at).limit(limit).offset(offset)
    )
    items = res.scalars().all()
    # prefer sort_order then created_at
    items.sort(key=lambda n: (n.sort_order, n.created_at))
    return items




@router.get("/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _ensure_owned_note(db, current_user.id, note_id)


@router.patch("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = await _ensure_owned_note(db, current_user.id, note_id)
    
    if payload.title is not None:
        note.title = payload.title
    if payload.body is not None:
        note.body = payload.body
    if payload.note_list_id is not None:
        # Validate new note list exists and belongs to user
        await _ensure_owned_note_list(db, current_user.id, payload.note_list_id)
        note.note_list_id = payload.note_list_id
        # If moving to new list, clear parent_id to avoid cross-list parent issues
        if payload.parent_id is None:
            note.parent_id = None
    if payload.parent_id is not None:
        target_list_id = payload.note_list_id if payload.note_list_id is not None else note.note_list_id
        await _validate_parent_note(db, current_user.id, payload.parent_id, target_list_id)
        await _check_circular_reference(db, note_id, payload.parent_id)
        note.parent_id = payload.parent_id
    if payload.sort_order is not None:
        note.sort_order = payload.sort_order
    
    await db.commit()
    await db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = await _ensure_owned_note(db, current_user.id, note_id)
    await db.delete(note)
    await db.commit()
    return None


@router.get("/{note_id}/children", response_model=list[NoteOut])
async def get_note_children(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_owned_note(db, current_user.id, note_id)
    res = await db.execute(
        select(Note).where(Note.parent_id == note_id).order_by(Note.created_at)
    )
    return res.scalars().all()


@router.post("/{note_id}/children", response_model=NoteOut, status_code=201)
async def create_child_note(
    note_id: uuid.UUID,
    payload: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parent_note = await _ensure_owned_note(db, current_user.id, note_id)
    
    if payload.note_list_id != parent_note.note_list_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="child_note_must_belong_to_same_note_list_as_parent"
        )
    
    note = Note(
        note_list_id=payload.note_list_id,
        title=payload.title,
        body=payload.body,
        parent_id=note_id
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/{note_id}/tags", response_model=list)
async def get_note_tags(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_owned_note(db, current_user.id, note_id)
    res = await db.execute(
        select(Tag)
        .join(tag_notes, Tag.id == tag_notes.c.tag_id)
        .where(tag_notes.c.note_id == note_id)
    )
    return res.scalars().all()


@router.post("/{note_id}/tags/{tag_id}", status_code=201)
async def attach_tag_to_note(
    note_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = await _ensure_owned_note(db, current_user.id, note_id)
    
    # Verify tag belongs to user
    res = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.owner_id == current_user.id)
    )
    tag = res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tag_not_found")

    # Enforce allowed TagLists: union of taglists on this note's list and its ancestors
    effective: set[uuid.UUID] = set()
    current_id = note.note_list_id
    while current_id is not None:
        tl_res = await db.execute(
            select(note_list_taglists.c.tag_list_id).where(note_list_taglists.c.note_list_id == current_id)
        )
        effective.update([row for row in tl_res.scalars().all()])
        parent_res = await db.execute(select(NoteList.parent_list_id).where(NoteList.id == current_id))
        current_id = parent_res.scalar_one_or_none()
    # If any taglists are configured in ancestry, require tag.tag_list_id to be among them
    if effective and (tag.tag_list_id not in effective):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tag_not_allowed_for_list")
    
    # Check if association already exists
    existing = await db.execute(
        select(tag_notes).where(
            (tag_notes.c.note_id == note_id) & (tag_notes.c.tag_id == tag_id)
        )
    )
    if not existing.first():
        await db.execute(
            tag_notes.insert().values(note_id=note_id, tag_id=tag_id)
        )
        await db.commit()
    
    return {"message": "tag_attached"}


@router.delete("/{note_id}/tags/{tag_id}", status_code=204)
async def detach_tag_from_note(
    note_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_owned_note(db, current_user.id, note_id)
    
    # Verify tag belongs to user
    res = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.owner_id == current_user.id)
    )
    tag = res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tag_not_found")
    
    # Remove association if it exists
    await db.execute(
        tag_notes.delete().where(
            (tag_notes.c.note_id == note_id) & (tag_notes.c.tag_id == tag_id)
        )
    )
    await db.commit()
    
    return None


@router.get("/{note_id}/links", response_model=dict)
async def get_note_links(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_owned_note(db, current_user.id, note_id)
    
    # Get notes this note links to
    linked_to_res = await db.execute(
        select(Note)
        .join(note_links, Note.id == note_links.c.target_note_id)
        .where(note_links.c.source_note_id == note_id)
    )
    
    # Get notes that link to this note
    linked_from_res = await db.execute(
        select(Note)
        .join(note_links, Note.id == note_links.c.source_note_id)
        .where(note_links.c.target_note_id == note_id)
    )
    
    return {
        "linked_to": linked_to_res.scalars().all(),
        "linked_from": linked_from_res.scalars().all()
    }


@router.post("/{note_id}/links/{target_note_id}", status_code=201)
async def link_notes(
    note_id: uuid.UUID,
    target_note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_owned_note(db, current_user.id, note_id)
    await _ensure_owned_note(db, current_user.id, target_note_id)
    
    # Check if link already exists
    existing = await db.execute(
        select(note_links).where(
            (note_links.c.source_note_id == note_id) & 
            (note_links.c.target_note_id == target_note_id)
        )
    )
    if not existing.first():
        await db.execute(
            note_links.insert().values(
                source_note_id=note_id, 
                target_note_id=target_note_id
            )
        )
        await db.commit()
    
    return {"message": "notes_linked"}


@router.delete("/{note_id}/links/{target_note_id}", status_code=204)
async def unlink_notes(
    note_id: uuid.UUID,
    target_note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_owned_note(db, current_user.id, note_id)
    await _ensure_owned_note(db, current_user.id, target_note_id)
    
    # Remove link if it exists
    await db.execute(
        note_links.delete().where(
            (note_links.c.source_note_id == note_id) & 
            (note_links.c.target_note_id == target_note_id)
        )
    )
    await db.commit()
    
    return None


# Note-Task Relationship Endpoints

async def _get_owned_task_or_404(db: AsyncSession, owner_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    from app.models.task_list import TaskList
    res = await db.execute(
        select(Task).join(TaskList).where(Task.id == task_id, TaskList.owner_id == owner_id)
    )
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task_not_found")
    return task


@router.get("/{note_id}/tasks", response_model=list[dict])
async def list_note_tasks(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = await _ensure_owned_note(db, current_user.id, note_id)
    res = await db.execute(
        select(Task).join(note_tasks, note_tasks.c.task_id == Task.id).where(note_tasks.c.note_id == note.id)
    )
    tasks = res.scalars().all()
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "description": t.description,
            "status": t.status.value,
            "priority": t.priority.value,
            "list_id": str(t.list_id),
            "due_at": t.due_at.isoformat() if t.due_at else None,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        }
        for t in tasks
    ]


@router.post("/{note_id}/tasks/{task_id}", status_code=204)
async def attach_task_to_note(
    note_id: uuid.UUID,
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = await _ensure_owned_note(db, current_user.id, note_id)
    task = await _get_owned_task_or_404(db, current_user.id, task_id)
    
    # check if already linked
    existing = await db.execute(
        select(note_tasks.c.note_id).where(
            note_tasks.c.note_id == note.id, note_tasks.c.task_id == task.id
        )
    )
    if existing.first() is None:
        await db.execute(note_tasks.insert().values(note_id=note.id, task_id=task.id))
        await db.commit()
    return None


@router.delete("/{note_id}/tasks/{task_id}", status_code=204)
async def detach_task_from_note(
    note_id: uuid.UUID,
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = await _ensure_owned_note(db, current_user.id, note_id)
    task = await _get_owned_task_or_404(db, current_user.id, task_id)
    
    await db.execute(
        note_tasks.delete().where(note_tasks.c.note_id == note.id, note_tasks.c.task_id == task.id)
    )
    await db.commit()
    return None
