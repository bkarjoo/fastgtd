import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select, asc, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_db
from app.api.auth import get_current_user
from app.models.task import Task
from app.models.task_list import TaskList
from app.models.default_task_list import DefaultTaskList
from app.models.user import User
from app.models.enums import TaskPriority, TaskStatus
from app.models.tag import Tag
from app.models.associations import task_tags, task_notes, task_list_taglists
from app.models.tag_list import TagList
from app.models.note import Note
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from pydantic import BaseModel

try:
    # python-dateutil for RFC 5545 RRULE parsing/expansion
    from dateutil.rrule import rrulestr
except Exception:  # pragma: no cover - allow running even if not installed yet
    rrulestr = None


router = APIRouter(prefix="/tasks", tags=["tasks"]) 


async def _ensure_list_owned(db: AsyncSession, owner_id: uuid.UUID, list_id: uuid.UUID) -> TaskList:
    res = await db.execute(select(TaskList).where(TaskList.id == list_id, TaskList.owner_id == owner_id))
    lst = res.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="list_not_found")
    return lst


async def _get_or_create_default_list_id(db: AsyncSession, owner_id: uuid.UUID) -> uuid.UUID:
    # Try mapping
    res = await db.execute(select(DefaultTaskList.task_list_id).where(DefaultTaskList.user_id == owner_id))
    tl_id = res.scalar_one_or_none()
    if tl_id:
        return tl_id
    # Fallback to system root for owner, create mapping
    res = await db.execute(select(TaskList.id).where(TaskList.owner_id == owner_id, TaskList.is_system_root == True))
    root_id = res.scalar_one_or_none()
    if root_id is None:
        # create a system root if somehow missing
        root = TaskList(owner_id=owner_id, name="__ROOT__", description="System root", is_system_root=True)
        db.add(root)
        await db.commit()
        await db.refresh(root)
        root_id = root.id
    # insert mapping
    db.add(DefaultTaskList(user_id=owner_id, task_list_id=root_id))
    await db.commit()
    return root_id


class TaskCreateInDefault(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_at: datetime | None = None
    parent_id: uuid.UUID | None = None
    sort_order: int | None = 0
    recurrence_rule: str | None = None
    recurrence_anchor: datetime | None = None


async def _get_owned_task_or_404(db: AsyncSession, owner_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    res = await db.execute(
        select(Task).join(TaskList).where(Task.id == task_id, TaskList.owner_id == owner_id)
    )
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task_not_found")
    return task


@router.post("", response_model=TaskOut, status_code=201)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_list_owned(db, current_user.id, payload.list_id)
    parent_id = payload.parent_id
    if parent_id is not None:
        parent = await _get_owned_task_or_404(db, current_user.id, parent_id)
        if parent.list_id != payload.list_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="parent_list_mismatch")

    task = Task(
        list_id=payload.list_id,
        parent_id=payload.parent_id,
        title=payload.title,
        description=payload.description,
        status=payload.status or TaskStatus.todo,
        priority=payload.priority or TaskPriority.medium,
        due_at=payload.due_at,
        earliest_start_at=payload.earliest_start_at,
        sort_order=payload.sort_order or 0,
        recurrence_rule=payload.recurrence_rule,
        recurrence_anchor=payload.recurrence_anchor,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/default", response_model=TaskOut, status_code=201)
async def create_task_in_default(
    payload: TaskCreateInDefault,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    list_id = await _get_or_create_default_list_id(db, current_user.id)
    # Optional: determine next sort_order by counting tasks in default list
    # We rely on client-provided sort_order if present; otherwise keep provided default
    task = Task(
        list_id=list_id,
        parent_id=payload.parent_id,
        title=payload.title,
        description=payload.description,
        status=payload.status or TaskStatus.todo,
        priority=payload.priority or TaskPriority.medium,
        due_at=payload.due_at,
        sort_order=payload.sort_order or 0,
        recurrence_rule=payload.recurrence_rule,
        recurrence_anchor=payload.recurrence_anchor,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    response: Response,
    list_id: uuid.UUID | None = None,
    status_: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    archived: bool | None = False,
    due_before: datetime | None = None,
    due_after: datetime | None = None,
    has_due: bool | None = None,
    earliest_start_before: datetime | None = None,
    earliest_start_after: datetime | None = None,
    has_earliest_start: bool | None = None,
    ready_only: bool | None = None,
    tag_id: uuid.UUID | None = None,
    q: str | None = None,
    order_by: str = "sort_order",  # one of: sort_order, created_at, due_at, priority
    order_dir: str = "asc",  # asc|desc
    limit: int = 50,
    offset: int = 0,
    include_total: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Task).join(TaskList).where(TaskList.owner_id == current_user.id)
    if list_id is not None:
        stmt = stmt.where(Task.list_id == list_id)
    if status_ is not None:
        stmt = stmt.where(Task.status == status_)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    if archived is not None:
        stmt = stmt.where(Task.archived == archived)
    if due_before is not None:
        stmt = stmt.where(Task.due_at <= due_before)
    if due_after is not None:
        stmt = stmt.where(Task.due_at >= due_after)
    if has_due:
        stmt = stmt.where(Task.due_at.isnot(None))
    if earliest_start_before is not None:
        stmt = stmt.where(Task.earliest_start_at <= earliest_start_before)
    if earliest_start_after is not None:
        stmt = stmt.where(Task.earliest_start_at >= earliest_start_after)
    if has_earliest_start:
        stmt = stmt.where(Task.earliest_start_at.isnot(None))
    if ready_only:
        # include tasks with no earliest_start_at or those whose time has arrived
        stmt = stmt.where((Task.earliest_start_at.is_(None)) | (Task.earliest_start_at <= func.now()))
    if tag_id is not None:
        # filter tasks by tag
        stmt = stmt.join(task_tags, task_tags.c.task_id == Task.id).where(task_tags.c.tag_id == tag_id)
    if q:
        ilike = f"%{q}%"
        stmt = stmt.where((Task.title.ilike(ilike)) | (Task.description.ilike(ilike)))

    # ordering
    order_map = {
        "sort_order": Task.sort_order,
        "created_at": Task.created_at,
        "due_at": Task.due_at,
        "earliest_start_at": Task.earliest_start_at,
        "priority": Task.priority,
    }
    col = order_map.get(order_by, Task.sort_order)
    direction = desc if order_dir.lower() == "desc" else asc
    stmt = stmt.order_by(direction(col), Task.created_at).limit(limit).offset(offset)
    res = await db.execute(stmt)
    items = res.scalars().all()

    if include_total:
        # Build count query with same filters
        from sqlalchemy import distinct

        base = select(func.count(Task.id)).join(TaskList).where(TaskList.owner_id == current_user.id)
        if list_id is not None:
            base = base.where(Task.list_id == list_id)
        if status_ is not None:
            base = base.where(Task.status == status_)
        if priority is not None:
            base = base.where(Task.priority == priority)
        if archived is not None:
            base = base.where(Task.archived == archived)
        if due_before is not None:
            base = base.where(Task.due_at <= due_before)
        if due_after is not None:
            base = base.where(Task.due_at >= due_after)
        if has_due:
            base = base.where(Task.due_at.isnot(None))
        if tag_id is not None:
            base = select(func.count(distinct(Task.id))).join(TaskList).join(task_tags, task_tags.c.task_id == Task.id).where(
                TaskList.owner_id == current_user.id, task_tags.c.tag_id == tag_id
            )
            if list_id is not None:
                base = base.where(Task.list_id == list_id)
            if status_ is not None:
                base = base.where(Task.status == status_)
            if priority is not None:
                base = base.where(Task.priority == priority)
            if archived is not None:
                base = base.where(Task.archived == archived)
            if due_before is not None:
                base = base.where(Task.due_at <= due_before)
            if due_after is not None:
                base = base.where(Task.due_at >= due_after)
        if q:
            ilike = f"%{q}%"
            base = base.where((Task.title.ilike(ilike)) | (Task.description.ilike(ilike)))
        total_res = await db.execute(base)
        response.headers["X-Total-Count"] = str(total_res.scalar_one())
    return items


@router.get("/{task_id}/tags", response_model=list[dict])
async def list_task_tags(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await _get_owned_task_or_404(db, current_user.id, task_id)
    res = await db.execute(
        select(Tag).join(task_tags, task_tags.c.tag_id == Tag.id).where(task_tags.c.task_id == task.id)
    )
    tags = res.scalars().all()
    # simple projection matching TagOut without re-import to avoid cycles
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "color": t.color,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
        for t in tags
    ]


@router.post("/{task_id}/tags/{tag_id}", status_code=204)
async def attach_tag(
    task_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await _get_owned_task_or_404(db, current_user.id, task_id)
    # ensure tag belongs to user
    res = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.owner_id == current_user.id))
    tag = res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tag_not_found")

    # Enforce allowed TagLists: union over task's list and ancestors
    effective: set[uuid.UUID] = set()
    current_id = task.list_id
    while current_id is not None:
        tl_res = await db.execute(
            select(task_list_taglists.c.tag_list_id).where(task_list_taglists.c.task_list_id == current_id)
        )
        effective.update([row for row in tl_res.scalars().all()])
        parent_res = await db.execute(select(TaskList.parent_list_id).where(TaskList.id == current_id))
        current_id = parent_res.scalar_one_or_none()
    if effective and (tag.tag_list_id not in effective):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tag_not_allowed_for_list")

    # upsert-ish: check existence then insert
    res = await db.execute(
        select(task_tags.c.task_id).where(
            task_tags.c.task_id == task.id, task_tags.c.tag_id == tag.id
        )
    )
    exists_row = res.first()
    if not exists_row:
        await db.execute(task_tags.insert().values(task_id=task.id, tag_id=tag.id))
        await db.commit()
    return None


@router.delete("/{task_id}/tags/{tag_id}", status_code=204)
async def detach_tag(
    task_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await _get_owned_task_or_404(db, current_user.id, task_id)
    # ensure tag belongs to user
    res = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.owner_id == current_user.id))
    tag = res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tag_not_found")
    await db.execute(
        task_tags.delete().where(task_tags.c.task_id == task.id, task_tags.c.tag_id == tag.id)
    )
    await db.commit()
    return None


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_owned_task_or_404(db, current_user.id, task_id)


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await _get_owned_task_or_404(db, current_user.id, task_id)
    # handle list move if requested
    if payload.list_id is not None and payload.list_id != task.list_id:
        # disallow moving when task has a parent unless parent is being updated to match
        if payload.parent_id is None and task.parent_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot_move_task_with_parent")
        # ensure new list belongs to user
        await _ensure_list_owned(db, current_user.id, payload.list_id)
        # if parent is set, ensure it belongs to user and same target list
        if payload.parent_id is not None:
            parent = await _get_owned_task_or_404(db, current_user.id, payload.parent_id)
            if parent.list_id != payload.list_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="parent_list_mismatch")
        # ensure no children exist to avoid partial tree move
        children_res = await db.execute(select(Task.id).where(Task.parent_id == task.id))
        if children_res.first() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot_move_task_with_children")
        task.list_id = payload.list_id
    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.status is not None:
        task.status = payload.status
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.due_at is not None:
        task.due_at = payload.due_at
    if payload.earliest_start_at is not None:
        task.earliest_start_at = payload.earliest_start_at
    if payload.completed_at is not None:
        task.completed_at = payload.completed_at
    if payload.archived is not None:
        task.archived = payload.archived
    if payload.sort_order is not None:
        task.sort_order = payload.sort_order
    if payload.recurrence_rule is not None:
        task.recurrence_rule = payload.recurrence_rule
    if payload.recurrence_anchor is not None:
        task.recurrence_anchor = payload.recurrence_anchor
    if payload.parent_id is not None:
        if payload.parent_id == task.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot_parent_self")
        parent = await _get_owned_task_or_404(db, current_user.id, payload.parent_id)
        if parent.list_id != task.list_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="parent_list_mismatch")
        task.parent_id = payload.parent_id
    # If status transitioned to done and completed_at is not set, stamp it now
    if payload.status == TaskStatus.done and task.completed_at is None and payload.completed_at is None:
        task.completed_at = datetime.now(timezone.utc)

    # Recurrence: if task has an RRULE, and it has just been completed, spawn next occurrence
    new_task = None
    if task.recurrence_rule and rrulestr is not None:
        # Trigger when completion timestamp is present after updates
        just_completed = task.completed_at is not None and (
            payload.completed_at is not None or payload.status == TaskStatus.done
        )
        if just_completed:
            # Determine anchor dtstart for rule
            anchor = task.recurrence_anchor or task.due_at or task.created_at
            try:
                rule = rrulestr(task.recurrence_rule, dtstart=anchor)
                # After the completion time, schedule next occurrence
                base = task.completed_at or datetime.now(timezone.utc)
                next_dt = rule.after(base, inc=False)
            except Exception:
                next_dt = None
            if next_dt is not None:
                new_task = Task(
                    list_id=task.list_id,
                    parent_id=task.parent_id,
                    title=task.title,
                    description=task.description,
                    status=TaskStatus.todo,
                    priority=task.priority,
                    due_at=next_dt,
                    sort_order=0,
                    recurrence_rule=task.recurrence_rule,
                    recurrence_anchor=anchor,
                )
                db.add(new_task)

    await db.commit()
    # if we created a new task, refresh both; otherwise refresh current
    await db.refresh(task)
    if new_task is not None:
        await db.refresh(new_task)
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await _get_owned_task_or_404(db, current_user.id, task_id)
    await db.delete(task)
    await db.commit()
    return None


# Task-Note Relationship Endpoints

@router.get("/{task_id}/notes", response_model=list[dict])
async def list_task_notes(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await _get_owned_task_or_404(db, current_user.id, task_id)
    res = await db.execute(
        select(Note).join(task_notes, task_notes.c.note_id == Note.id).where(task_notes.c.task_id == task.id)
    )
    notes = res.scalars().all()
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "body": n.body,
            "note_list_id": str(n.note_list_id),
            "created_at": n.created_at.isoformat(),
            "updated_at": n.updated_at.isoformat(),
        }
        for n in notes
    ]


async def _get_owned_note_or_404(db: AsyncSession, owner_id: uuid.UUID, note_id: uuid.UUID) -> Note:
    from app.models.note_list import NoteList
    res = await db.execute(
        select(Note).join(NoteList).where(Note.id == note_id, NoteList.owner_id == owner_id)
    )
    note = res.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="note_not_found")
    return note


@router.post("/{task_id}/notes/{note_id}", status_code=204)
async def attach_note_to_task(
    task_id: uuid.UUID,
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await _get_owned_task_or_404(db, current_user.id, task_id)
    note = await _get_owned_note_or_404(db, current_user.id, note_id)
    
    # check if already linked
    existing = await db.execute(
        select(task_notes.c.task_id).where(
            task_notes.c.task_id == task.id, task_notes.c.note_id == note.id
        )
    )
    if existing.first() is None:
        await db.execute(task_notes.insert().values(task_id=task.id, note_id=note.id))
        await db.commit()
    return None


@router.delete("/{task_id}/notes/{note_id}", status_code=204)
async def detach_note_from_task(
    task_id: uuid.UUID,
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await _get_owned_task_or_404(db, current_user.id, task_id)
    note = await _get_owned_note_or_404(db, current_user.id, note_id)
    
    await db.execute(
        task_notes.delete().where(task_notes.c.task_id == task.id, task_notes.c.note_id == note.id)
    )
    await db.commit()
    return None
