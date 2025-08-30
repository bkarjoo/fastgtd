import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_db
from app.api.auth import get_current_user
from app.models.tag_list import TagList
from app.models.default_tag_list import DefaultTagList
from app.models.tag import Tag
from app.models.user import User
from app.models.associations import tag_list_tags
from app.schemas.tag_list import TagListCreate, TagListUpdate, TagListOut, TagListParentUpdate
from app.schemas.tag import TagOut


router = APIRouter(prefix="/taglists", tags=["taglists"])


async def _get_or_create_system_root(db: AsyncSession, owner_id: uuid.UUID) -> TagList:
    res = await db.execute(select(TagList).where(TagList.owner_id == owner_id, TagList.is_system_root == True))
    root = res.scalar_one_or_none()
    if root is None:
        root = TagList(owner_id=owner_id, name='__TAG_ROOT__', description='System tag root', parent_list_id=None, sort_order=0, is_system_root=True)
        db.add(root)
        await db.commit()
        await db.refresh(root)
    return root


@router.post("", response_model=TagListOut, status_code=201)
async def create_tag_list(
    payload: TagListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    root = await _get_or_create_system_root(db, current_user.id)
    tl = TagList(
        owner_id=current_user.id,
        parent_list_id=root.id,
        name=payload.name,
        description=payload.description,
        sort_order=payload.sort_order or 0,
    )
    db.add(tl)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(tl)
    return tl


@router.get("", response_model=list[TagListOut])
async def list_tag_lists(
    response: Response,
    limit: int = 100,
    offset: int = 0,
    include_total: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(TagList).where(TagList.owner_id == current_user.id, TagList.is_system_root == False).order_by(TagList.sort_order, TagList.created_at)
    stmt = stmt.limit(limit).offset(offset)
    res = await db.execute(stmt)
    items = res.scalars().all()
    root = await _get_or_create_system_root(db, current_user.id)
    items = [
        TagListOut(
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
        total_stmt = select(func.count()).select_from(TagList).where(TagList.owner_id == current_user.id, TagList.is_system_root == False)
        total_res = await db.execute(total_stmt)
        response.headers["X-Total-Count"] = str(total_res.scalar_one())
    return items


# Static helper endpoints must be declared before dynamic /{tag_list_id}

@router.get("/root", response_model=TagListOut)
async def get_tag_root(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    root = await _get_or_create_system_root(db, current_user.id)
    return TagListOut(
        id=root.id,
        owner_id=root.owner_id,
        parent_list_id=None,
        name=root.name,
        description=root.description,
        sort_order=root.sort_order,
        created_at=root.created_at,
        updated_at=root.updated_at,
    )


@router.get("/default", response_model=TagListOut)
async def get_default_tag_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(DefaultTagList.tag_list_id).where(DefaultTagList.user_id == current_user.id))
    tl_id = res.scalar_one_or_none()
    if tl_id is not None:
        res2 = await db.execute(select(TagList).where(TagList.id == tl_id, TagList.owner_id == current_user.id))
        tl = res2.scalar_one_or_none()
        if tl is not None:
            return tl
    root = await _get_or_create_system_root(db, current_user.id)
    await db.execute(
        pg_insert(DefaultTagList.__table__).values(user_id=current_user.id, tag_list_id=root.id).on_conflict_do_update(
            index_elements=[DefaultTagList.__table__.c.user_id],
            set_={"tag_list_id": root.id},
        )
    )
    await db.commit()
    return root


async def _get_owned_tag_list_or_404(db: AsyncSession, owner_id: uuid.UUID, tag_list_id: uuid.UUID) -> TagList:
    res = await db.execute(select(TagList).where(TagList.id == tag_list_id, TagList.owner_id == owner_id))
    tl = res.scalar_one_or_none()
    if not tl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tag_list_not_found")
    return tl


@router.get("/{tag_list_id}", response_model=TagListOut)
async def get_tag_list(
    tag_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tl = await _get_owned_tag_list_or_404(db, current_user.id, tag_list_id)
    root = await _get_or_create_system_root(db, current_user.id)
    return TagListOut(
        id=tl.id,
        owner_id=tl.owner_id,
        parent_list_id=(None if tl.parent_list_id == root.id else tl.parent_list_id),
        name=tl.name,
        description=tl.description,
        sort_order=tl.sort_order,
        created_at=tl.created_at,
        updated_at=tl.updated_at,
    )


@router.get("/root", response_model=TagListOut)
async def get_tag_root(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    root = await _get_or_create_system_root(db, current_user.id)
    return TagListOut(
        id=root.id,
        owner_id=root.owner_id,
        parent_list_id=None,
        name=root.name,
        description=root.description,
        sort_order=root.sort_order,
        created_at=root.created_at,
        updated_at=root.updated_at,
    )


@router.get("/default", response_model=TagListOut)
async def get_default_tag_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(DefaultTagList.tag_list_id).where(DefaultTagList.user_id == current_user.id))
    tl_id = res.scalar_one_or_none()
    if tl_id is not None:
        res2 = await db.execute(select(TagList).where(TagList.id == tl_id, TagList.owner_id == current_user.id))
        tl = res2.scalar_one_or_none()
        if tl is not None:
            return tl
    root = await _get_or_create_system_root(db, current_user.id)
    await db.execute(
        pg_insert(DefaultTagList.__table__).values(user_id=current_user.id, tag_list_id=root.id).on_conflict_do_update(
            index_elements=[DefaultTagList.__table__.c.user_id],
            set_={"tag_list_id": root.id},
        )
    )
    await db.commit()
    return root


@router.patch("/{tag_list_id}", response_model=TagListOut)
async def update_tag_list(
    tag_list_id: uuid.UUID,
    payload: TagListUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tl = await _get_owned_tag_list_or_404(db, current_user.id, tag_list_id)
    if payload.name is not None:
        tl.name = payload.name
    if payload.description is not None:
        tl.description = payload.description
    if payload.sort_order is not None:
        tl.sort_order = payload.sort_order
    await db.commit()
    await db.refresh(tl)
    return tl


@router.delete("/{tag_list_id}", status_code=204)
async def delete_tag_list(
    tag_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tl = await _get_owned_tag_list_or_404(db, current_user.id, tag_list_id)
    await db.delete(tl)
    await db.commit()
    return None


@router.get("/{tag_list_id}/tags", response_model=list[TagOut])
async def list_tags_in_tag_list(
    tag_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_tag_list_or_404(db, current_user.id, tag_list_id)
    res = await db.execute(select(Tag).where(Tag.owner_id == current_user.id, Tag.tag_list_id == tag_list_id).order_by(Tag.sort_order, Tag.name))
    return res.scalars().all()


# Hierarchy Management Endpoints

@router.get("/{tag_list_id}/children", response_model=list[TagListOut])
async def get_tag_list_children(
    tag_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_tag_list_or_404(db, current_user.id, tag_list_id)
    res = await db.execute(
        select(TagList).where(TagList.parent_list_id == tag_list_id).order_by(TagList.sort_order, TagList.created_at)
    )
    return res.scalars().all()


@router.post("/{tag_list_id}/children", response_model=TagListOut, status_code=201)
async def create_child_tag_list(
    tag_list_id: uuid.UUID,
    payload: TagListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parent_list = await _get_owned_tag_list_or_404(db, current_user.id, tag_list_id)
    
    child_list = TagList(
        owner_id=current_user.id,
        parent_list_id=tag_list_id,
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


async def _check_circular_reference_tag_list(db: AsyncSession, tag_list_id: uuid.UUID, parent_id: uuid.UUID) -> None:
    current_parent_id = parent_id
    visited = {tag_list_id}
    
    while current_parent_id:
        if current_parent_id in visited:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="circular_reference_detected"
            )
        visited.add(current_parent_id)
        
        res = await db.execute(select(TagList.parent_list_id).where(TagList.id == current_parent_id))
        current_parent_id = res.scalar_one_or_none()


@router.patch("/{tag_list_id}/parent", response_model=TagListOut)
async def update_tag_list_parent(
    tag_list_id: uuid.UUID,
    payload: TagListParentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag_list = await _get_owned_tag_list_or_404(db, current_user.id, tag_list_id)
    
    if payload.parent_list_id:
        await _get_owned_tag_list_or_404(db, current_user.id, payload.parent_list_id)
        await _check_circular_reference_tag_list(db, tag_list_id, payload.parent_list_id)
    if payload.parent_list_id:
        tag_list.parent_list_id = payload.parent_list_id
    else:
        root = await _get_or_create_system_root(db, current_user.id)
        tag_list.parent_list_id = root.id
    await db.commit()
    await db.refresh(tag_list)
    root = await _get_or_create_system_root(db, current_user.id)
    return TagListOut(
        id=tag_list.id,
        owner_id=tag_list.owner_id,
        parent_list_id=(None if tag_list.parent_list_id == root.id else tag_list.parent_list_id),
        name=tag_list.name,
        description=tag_list.description,
        sort_order=tag_list.sort_order,
        created_at=tag_list.created_at,
        updated_at=tag_list.updated_at,
    )


@router.post("/{tag_list_id}/default", status_code=204)
async def set_default_tag_list(
    tag_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tl = await _get_owned_tag_list_or_404(db, current_user.id, tag_list_id)
    await db.execute(
        pg_insert(DefaultTagList.__table__).values(user_id=current_user.id, tag_list_id=tl.id).on_conflict_do_update(
            index_elements=[DefaultTagList.__table__.c.user_id],
            set_={"tag_list_id": tl.id},
        )
    )
    await db.commit()
    return None


# TagList Tagging Endpoints

async def _get_owned_tag_or_404(db: AsyncSession, owner_id: uuid.UUID, tag_id: uuid.UUID) -> Tag:
    res = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.owner_id == owner_id))
    tag = res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tag_not_found")
    return tag


@router.get("/{tag_list_id}/applied-tags", response_model=list[TagOut])
async def list_tag_list_applied_tags(
    tag_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag_list = await _get_owned_tag_list_or_404(db, current_user.id, tag_list_id)
    res = await db.execute(
        select(Tag).join(tag_list_tags, tag_list_tags.c.tag_id == Tag.id).where(tag_list_tags.c.tag_list_id == tag_list.id, Tag.owner_id == current_user.id)
    )
    return res.scalars().all()


@router.post("/{tag_list_id}/applied-tags/{tag_id}", status_code=204)
async def attach_tag_to_tag_list(
    tag_list_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag_list = await _get_owned_tag_list_or_404(db, current_user.id, tag_list_id)
    await _get_owned_tag_or_404(db, current_user.id, tag_id)
    await db.execute(pg_insert(tag_list_tags).values(tag_list_id=tag_list.id, tag_id=tag_id).on_conflict_do_nothing())
    await db.commit()
    return None


@router.delete("/{tag_list_id}/applied-tags/{tag_id}", status_code=204)
async def detach_tag_from_tag_list(
    tag_list_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag_list = await _get_owned_tag_list_or_404(db, current_user.id, tag_list_id)
    await _get_owned_tag_or_404(db, current_user.id, tag_id)
    await db.execute(tag_list_tags.delete().where(tag_list_tags.c.tag_list_id == tag_list.id, tag_list_tags.c.tag_id == tag_id))
    await db.commit()
    return None
