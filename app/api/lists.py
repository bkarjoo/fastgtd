import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_db
from app.api.auth import get_current_user
from app.models.task_list import TaskList
from app.models.tag import Tag
from app.models.associations import list_tags, task_list_taglists
from app.models.tag_list import TagList
from app.schemas.tag import TagOut
from app.schemas.tag_list import TagListOut
from app.schemas.list import TaskListCreate, TaskListUpdate, TaskListOut, TaskListParentUpdate
from app.models.user import User
from app.models.default_task_list import DefaultTaskList


router = APIRouter(prefix="/lists", tags=["lists"])


async def _get_or_create_system_root(db: AsyncSession, owner_id: uuid.UUID) -> TaskList:
    res = await db.execute(select(TaskList).where(TaskList.owner_id == owner_id, TaskList.is_system_root == True))
    root = res.scalar_one_or_none()
    if root is None:
        # Fallback creation path if migration didn't run; keep invisible
        root = TaskList(owner_id=owner_id, name="__ROOT__", description="System root", parent_list_id=None, sort_order=0, is_system_root=True)
        db.add(root)
        await db.commit()
        await db.refresh(root)
    return root


@router.post("", response_model=TaskListOut, status_code=201)
async def create_list(
    payload: TaskListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Create as a top-level list by assigning the (invisible) system root as parent
    root = await _get_or_create_system_root(db, current_user.id)
    lst = TaskList(
        owner_id=current_user.id,
        parent_list_id=root.id,
        name=payload.name,
        description=payload.description,
        sort_order=payload.sort_order or 0,
    )
    db.add(lst)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(lst)
    # Present top-level lists as having no parent to the client
    return TaskListOut(
        id=lst.id,
        owner_id=lst.owner_id,
        parent_list_id=None,
        name=lst.name,
        description=lst.description,
        sort_order=lst.sort_order,
        created_at=lst.created_at,
        updated_at=lst.updated_at,
    )


@router.get("", response_model=list[TaskListOut])
async def list_lists(
    response: Response,
    tag_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
    include_total: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(TaskList)
        .where(TaskList.owner_id == current_user.id, TaskList.is_system_root == False)
    )
    if tag_id is not None:
        stmt = stmt.join(list_tags, list_tags.c.list_id == TaskList.id).where(list_tags.c.tag_id == tag_id)
    stmt = stmt.order_by(TaskList.sort_order, TaskList.created_at).limit(limit).offset(offset)
    res = await db.execute(stmt)
    items = res.scalars().all()
    # Map system-root parent to None so frontend treats them as top-level
    root = await _get_or_create_system_root(db, current_user.id)
    projected = [
        TaskListOut(
            id=i.id,
            owner_id=i.owner_id,
            parent_list_id=(None if i.parent_list_id == root.id else i.parent_list_id),
            name=i.name,
            description=i.description,
            sort_order=i.sort_order,
            created_at=i.created_at,
            updated_at=i.updated_at,
        )
        for i in items
    ]
    if include_total:
        total_stmt = select(func.count()).select_from(TaskList).where(TaskList.owner_id == current_user.id, TaskList.is_system_root == False)
        if tag_id is not None:
            total_stmt = (
                select(func.count())
                .select_from(TaskList.__table__.join(list_tags, list_tags.c.list_id == TaskList.id))
                .where(TaskList.owner_id == current_user.id, TaskList.is_system_root == False, list_tags.c.tag_id == tag_id)
            )
        total_res = await db.execute(total_stmt)
        response.headers["X-Total-Count"] = str(total_res.scalar_one())
    return projected


# Static helper endpoints must be declared before dynamic /{list_id}

@router.get("/root", response_model=TaskListOut)
async def get_system_root(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    root = await _get_or_create_system_root(db, current_user.id)
    return TaskListOut(
        id=root.id,
        owner_id=root.owner_id,
        parent_list_id=None,
        name=root.name,
        description=root.description,
        sort_order=root.sort_order,
        created_at=root.created_at,
        updated_at=root.updated_at,
    )


@router.get("/root-children", response_model=list[TaskListOut])
async def get_root_children(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    root = await _get_or_create_system_root(db, current_user.id)
    res = await db.execute(
        select(TaskList)
        .where(TaskList.parent_list_id == root.id)
        .order_by(TaskList.sort_order, TaskList.created_at)
    )
    return res.scalars().all()


@router.get("/default", response_model=TaskListOut)
async def get_default_task_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Try existing mapping
    res = await db.execute(select(DefaultTaskList.task_list_id).where(DefaultTaskList.user_id == current_user.id))
    tl_id = res.scalar_one_or_none()
    if tl_id is not None:
        # Return the list if it still exists and is owned by user
        res2 = await db.execute(select(TaskList).where(TaskList.id == tl_id, TaskList.owner_id == current_user.id))
        lst = res2.scalar_one_or_none()
        if lst is not None:
            return lst
    # Fallback to system root and upsert mapping
    root = await _get_or_create_system_root(db, current_user.id)
    await db.execute(
        pg_insert(DefaultTaskList.__table__).values(user_id=current_user.id, task_list_id=root.id).on_conflict_do_update(
            index_elements=[DefaultTaskList.__table__.c.user_id],
            set_={"task_list_id": root.id},
        )
    )
    await db.commit()
    return root

 


 


 


 


 


async def _get_owned_list_or_404(db: AsyncSession, owner_id: uuid.UUID, list_id: uuid.UUID) -> TaskList:
    res = await db.execute(select(TaskList).where(TaskList.id == list_id, TaskList.owner_id == owner_id))
    lst = res.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="list_not_found")
    return lst


@router.get("/{list_id}", response_model=TaskListOut)
async def get_list(
    list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lst = await _get_owned_list_or_404(db, current_user.id, list_id)
    root = await _get_or_create_system_root(db, current_user.id)
    return TaskListOut(
        id=lst.id,
        owner_id=lst.owner_id,
        parent_list_id=(None if lst.parent_list_id == root.id else lst.parent_list_id),
        name=lst.name,
        description=lst.description,
        sort_order=lst.sort_order,
        created_at=lst.created_at,
        updated_at=lst.updated_at,
    )


 


@router.patch("/{list_id}", response_model=TaskListOut)
async def update_list(
    list_id: uuid.UUID,
    payload: TaskListUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lst = await _get_owned_list_or_404(db, current_user.id, list_id)
    if payload.name is not None:
        lst.name = payload.name
    if payload.description is not None:
        lst.description = payload.description
    if payload.sort_order is not None:
        lst.sort_order = payload.sort_order
    await db.commit()
    await db.refresh(lst)
    root = await _get_or_create_system_root(db, current_user.id)
    return TaskListOut(
        id=lst.id,
        owner_id=lst.owner_id,
        parent_list_id=(None if lst.parent_list_id == root.id else lst.parent_list_id),
        name=lst.name,
        description=lst.description,
        sort_order=lst.sort_order,
        created_at=lst.created_at,
        updated_at=lst.updated_at,
    )


@router.delete("/{list_id}", status_code=204)
async def delete_list(
    list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lst = await _get_owned_list_or_404(db, current_user.id, list_id)
    await db.delete(lst)
    await db.commit()
    return None




@router.get("/{list_id}/tags", response_model=list[TagOut])
async def list_list_tags(
    list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lst = await _get_owned_list_or_404(db, current_user.id, list_id)
    # explicit select to avoid lazy loading issues in async
    res = await db.execute(
        select(Tag).join(list_tags, list_tags.c.tag_id == Tag.id).where(list_tags.c.list_id == lst.id, Tag.owner_id == current_user.id)
    )
    return res.scalars().all()


# TagList association management for TaskLists

@router.get("/{list_id}/taglists", response_model=list[TagListOut])
async def list_task_list_taglists(
    list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lst = await _get_owned_list_or_404(db, current_user.id, list_id)
    res = await db.execute(
        select(TagList)
        .join(task_list_taglists, task_list_taglists.c.tag_list_id == TagList.id)
        .where(task_list_taglists.c.task_list_id == lst.id, TagList.owner_id == current_user.id)
        .order_by(TagList.sort_order, TagList.created_at)
    )
    return res.scalars().all()


@router.post("/{list_id}/taglists/{tag_list_id}", status_code=204)
async def attach_taglist_to_task_list(
    list_id: uuid.UUID,
    tag_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lst = await _get_owned_list_or_404(db, current_user.id, list_id)
    tl_res = await db.execute(select(TagList).where(TagList.id == tag_list_id, TagList.owner_id == current_user.id))
    if tl_res.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tag_list_not_found")
    await db.execute(
        pg_insert(task_list_taglists).values(task_list_id=lst.id, tag_list_id=tag_list_id).on_conflict_do_nothing()
    )
    await db.commit()
    return None


@router.delete("/{list_id}/taglists/{tag_list_id}", status_code=204)
async def detach_taglist_from_task_list(
    list_id: uuid.UUID,
    tag_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lst = await _get_owned_list_or_404(db, current_user.id, list_id)
    await db.execute(
        task_list_taglists.delete().where(
            task_list_taglists.c.task_list_id == lst.id,
            task_list_taglists.c.tag_list_id == tag_list_id,
        )
    )
    await db.commit()
    return None


async def _get_effective_taglist_ids_for_task_list(db: AsyncSession, owner_id: uuid.UUID, list_id: uuid.UUID) -> set[uuid.UUID]:
    # Allow traversal starting from any owned list, including system root
    res = await db.execute(select(TaskList).where(TaskList.id == list_id, TaskList.owner_id == owner_id))
    if res.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="list_not_found")
    effective: set[uuid.UUID] = set()
    current_id = list_id
    while current_id is not None:
        res = await db.execute(
            select(task_list_taglists.c.tag_list_id)
            .where(task_list_taglists.c.task_list_id == current_id)
        )
        effective.update([row for row in res.scalars().all()])
        parent_res = await db.execute(select(TaskList.parent_list_id).where(TaskList.id == current_id))
        current_id = parent_res.scalar_one_or_none()
    return effective


@router.get("/{list_id}/effective-taglists", response_model=list[TagListOut])
async def get_effective_taglists_for_task_list(
    list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ids = await _get_effective_taglist_ids_for_task_list(db, current_user.id, list_id)
    if not ids:
        return []
    res = await db.execute(select(TagList).where(TagList.owner_id == current_user.id, TagList.id.in_(list(ids))))
    return res.scalars().all()


@router.get("/{list_id}/available-tags", response_model=list[TagOut])
async def get_available_tags_for_task_list(
    list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ids = await _get_effective_taglist_ids_for_task_list(db, current_user.id, list_id)
    stmt = select(Tag).where(Tag.owner_id == current_user.id)
    if ids:
        stmt = stmt.where(Tag.tag_list_id.in_(list(ids)))
    stmt = stmt.order_by(Tag.name)
    res = await db.execute(stmt)
    return res.scalars().all()


async def _get_owned_tag_or_404(db: AsyncSession, owner_id: uuid.UUID, tag_id: uuid.UUID) -> Tag:
    res = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.owner_id == owner_id))
    tag = res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tag_not_found")
    return tag


@router.post("/{list_id}/tags/{tag_id}", status_code=204)
async def attach_tag_to_list(
    list_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lst = await _get_owned_list_or_404(db, current_user.id, list_id)
    await _get_owned_tag_or_404(db, current_user.id, tag_id)
    # insert into association; ignore duplicates
    await db.execute(pg_insert(list_tags).values(list_id=lst.id, tag_id=tag_id).on_conflict_do_nothing())
    await db.commit()
    return None


@router.delete("/{list_id}/tags/{tag_id}", status_code=204)
async def detach_tag_from_list(
    list_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lst = await _get_owned_list_or_404(db, current_user.id, list_id)
    await _get_owned_tag_or_404(db, current_user.id, tag_id)
    await db.execute(list_tags.delete().where(list_tags.c.list_id == lst.id, list_tags.c.tag_id == tag_id))
    await db.commit()
    return None


# Hierarchy Management Endpoints

@router.get("/{list_id}/children", response_model=list[TaskListOut])
async def get_list_children(
    list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_list_or_404(db, current_user.id, list_id)
    res = await db.execute(
        select(TaskList).where(TaskList.parent_list_id == list_id).order_by(TaskList.sort_order, TaskList.created_at)
    )
    return res.scalars().all()


 


@router.post("/{list_id}/default", status_code=204)
async def set_default_task_list(
    list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Allow setting any owned list (including system root)
    res = await db.execute(select(TaskList).where(TaskList.id == list_id, TaskList.owner_id == current_user.id))
    lst = res.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="list_not_found")
    # Upsert mapping
    await db.execute(
        pg_insert(DefaultTaskList.__table__).values(user_id=current_user.id, task_list_id=list_id).on_conflict_do_update(
            index_elements=[DefaultTaskList.__table__.c.user_id],
            set_={"task_list_id": list_id},
        )
    )
    await db.commit()
    return None


 


@router.post("/{list_id}/children", response_model=TaskListOut, status_code=201)
async def create_child_list(
    list_id: uuid.UUID,
    payload: TaskListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parent_list = await _get_owned_list_or_404(db, current_user.id, list_id)
    
    child_list = TaskList(
        owner_id=current_user.id,
        parent_list_id=list_id,
        name=payload.name,
        description=payload.description,
        sort_order=payload.sort_order or 0
    )
    db.add(child_list)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(child_list)
    return child_list


async def _check_circular_reference_list(db: AsyncSession, list_id: uuid.UUID, parent_id: uuid.UUID) -> None:
    current_parent_id = parent_id
    visited = {list_id}
    
    while current_parent_id:
        if current_parent_id in visited:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="circular_reference_detected"
            )
        visited.add(current_parent_id)
        
        res = await db.execute(select(TaskList.parent_list_id).where(TaskList.id == current_parent_id))
        current_parent_id = res.scalar_one_or_none()


@router.patch("/{list_id}/parent", response_model=TaskListOut)
async def update_list_parent(
    list_id: uuid.UUID,
    payload: TaskListParentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lst = await _get_owned_list_or_404(db, current_user.id, list_id)
    # Treat null as "move to top level" by assigning the invisible system root
    if payload.parent_list_id:
        await _get_owned_list_or_404(db, current_user.id, payload.parent_list_id)
        await _check_circular_reference_list(db, list_id, payload.parent_list_id)
        lst.parent_list_id = payload.parent_list_id
    else:
        root = await _get_or_create_system_root(db, current_user.id)
        lst.parent_list_id = root.id
    await db.commit()
    await db.refresh(lst)
    root = await _get_or_create_system_root(db, current_user.id)
    return TaskListOut(
        id=lst.id,
        owner_id=lst.owner_id,
        parent_list_id=(None if lst.parent_list_id == root.id else lst.parent_list_id),
        name=lst.name,
        description=lst.description,
        sort_order=lst.sort_order,
        created_at=lst.created_at,
        updated_at=lst.updated_at,
    )
