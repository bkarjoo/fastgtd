import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_db
from app.api.auth import get_current_user
from app.models.note_list import NoteList
from app.models.default_note_list import DefaultNoteList
from app.models.tag import Tag
from app.models.tag_list import TagList
from app.models.associations import note_list_tags, note_list_taglists
from app.schemas.tag import TagOut
from app.schemas.tag_list import TagListOut
from app.models.user import User
from app.schemas.note_list import NoteListCreate, NoteListUpdate, NoteListOut, NoteListParentUpdate


router = APIRouter(prefix="/note-lists", tags=["note-lists"])


async def _get_or_create_system_root(db: AsyncSession, owner_id: uuid.UUID) -> NoteList:
    res = await db.execute(select(NoteList).where(NoteList.owner_id == owner_id, NoteList.is_system_root == True))
    root = res.scalar_one_or_none()
    if root is None:
        root = NoteList(owner_id=owner_id, name='__NOTE_ROOT__', description='System note root', parent_list_id=None, sort_order=0, is_system_root=True)
        db.add(root)
        await db.commit()
        await db.refresh(root)
    return root


@router.post("", response_model=NoteListOut, status_code=201)
async def create_note_list(
    payload: NoteListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    root = await _get_or_create_system_root(db, current_user.id)
    note_list = NoteList(
        owner_id=current_user.id,
        parent_list_id=root.id,
        name=payload.name,
        description=payload.description,
        sort_order=payload.sort_order or 0
    )
    db.add(note_list)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(note_list)
    # Present as top-level (no parent) to client
    return NoteListOut(
        id=note_list.id,
        owner_id=note_list.owner_id,
        parent_list_id=None,
        name=note_list.name,
        description=note_list.description,
        sort_order=note_list.sort_order,
        created_at=note_list.created_at,
        updated_at=note_list.updated_at,
    )


@router.get("", response_model=list[NoteListOut])
async def list_note_lists(
    response: Response,
    tag_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
    include_total: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(NoteList)
        .where(NoteList.owner_id == current_user.id, NoteList.is_system_root == False)
    )
    if tag_id is not None:
        stmt = stmt.join(note_list_tags, note_list_tags.c.note_list_id == NoteList.id).where(note_list_tags.c.tag_id == tag_id)
    stmt = stmt.order_by(NoteList.sort_order, NoteList.created_at).limit(limit).offset(offset)
    res = await db.execute(stmt)
    items = res.scalars().all()
    root = await _get_or_create_system_root(db, current_user.id)
    # Project system root parent to None for clients
    items = [
        NoteListOut(
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
        total_stmt = select(func.count()).select_from(NoteList).where(NoteList.owner_id == current_user.id, NoteList.is_system_root == False)
        if tag_id is not None:
            total_stmt = (
                select(func.count())
                .select_from(NoteList.__table__.join(note_list_tags, note_list_tags.c.note_list_id == NoteList.id))
                .where(NoteList.owner_id == current_user.id, NoteList.is_system_root == False, note_list_tags.c.tag_id == tag_id)
            )
        total_res = await db.execute(total_stmt)
        response.headers["X-Total-Count"] = str(total_res.scalar_one())
    return items


# Static helper endpoints must be declared before dynamic /{note_list_id}

@router.get("/root", response_model=NoteListOut)
async def get_note_root(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    root = await _get_or_create_system_root(db, current_user.id)
    return NoteListOut(
        id=root.id,
        owner_id=root.owner_id,
        parent_list_id=None,
        name=root.name,
        description=root.description,
        sort_order=root.sort_order,
        created_at=root.created_at,
        updated_at=root.updated_at,
    )


@router.get("/default", response_model=NoteListOut)
async def get_default_note_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(DefaultNoteList.note_list_id).where(DefaultNoteList.user_id == current_user.id))
    nl_id = res.scalar_one_or_none()
    if nl_id is not None:
        res2 = await db.execute(select(NoteList).where(NoteList.id == nl_id, NoteList.owner_id == current_user.id))
        nl = res2.scalar_one_or_none()
        if nl is not None:
            return nl
    root = await _get_or_create_system_root(db, current_user.id)
    await db.execute(
        pg_insert(DefaultNoteList.__table__).values(user_id=current_user.id, note_list_id=root.id).on_conflict_do_update(
            index_elements=[DefaultNoteList.__table__.c.user_id],
            set_={"note_list_id": root.id},
        )
    )
    await db.commit()
    return root


# Static helper endpoints must be declared before dynamic /{note_list_id}

 


async def _get_owned_note_list_or_404(db: AsyncSession, owner_id: uuid.UUID, note_list_id: uuid.UUID) -> NoteList:
    res = await db.execute(select(NoteList).where(NoteList.id == note_list_id, NoteList.owner_id == owner_id))
    note_list = res.scalar_one_or_none()
    if not note_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="note_list_not_found")
    return note_list


@router.get("/{note_list_id}", response_model=NoteListOut)
async def get_note_list(
    note_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    nl = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    root = await _get_or_create_system_root(db, current_user.id)
    return NoteListOut(
        id=nl.id,
        owner_id=nl.owner_id,
        parent_list_id=(None if nl.parent_list_id == root.id else nl.parent_list_id),
        name=nl.name,
        description=nl.description,
        sort_order=nl.sort_order,
        created_at=nl.created_at,
        updated_at=nl.updated_at,
    )

 


@router.patch("/{note_list_id}", response_model=NoteListOut)
async def update_note_list(
    note_list_id: uuid.UUID,
    payload: NoteListUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_list = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    if payload.name is not None:
        note_list.name = payload.name
    if payload.description is not None:
        note_list.description = payload.description
    if payload.sort_order is not None:
        note_list.sort_order = payload.sort_order
    await db.commit()
    await db.refresh(note_list)
    return note_list


@router.delete("/{note_list_id}", status_code=204)
async def delete_note_list(
    note_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_list = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    await db.delete(note_list)
    await db.commit()
    return None


@router.get("/{note_list_id}/tags", response_model=list[TagOut])
async def list_note_list_tags(
    note_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_list = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    res = await db.execute(
        select(Tag).join(note_list_tags, note_list_tags.c.tag_id == Tag.id).where(note_list_tags.c.note_list_id == note_list.id, Tag.owner_id == current_user.id)
    )
    return res.scalars().all()


# TagList association management for NoteLists

@router.get("/{note_list_id}/taglists", response_model=list[TagListOut])
async def list_note_list_taglists(
    note_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_list = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    res = await db.execute(
        select(TagList)
        .join(note_list_taglists, note_list_taglists.c.tag_list_id == TagList.id)
        .where(note_list_taglists.c.note_list_id == note_list.id, TagList.owner_id == current_user.id)
        .order_by(TagList.sort_order, TagList.created_at)
    )
    return res.scalars().all()


@router.post("/{note_list_id}/taglists/{tag_list_id}", status_code=204)
async def attach_taglist_to_note_list(
    note_list_id: uuid.UUID,
    tag_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_list = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    # ensure taglist belongs to user
    tl_res = await db.execute(select(TagList).where(TagList.id == tag_list_id, TagList.owner_id == current_user.id))
    if tl_res.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tag_list_not_found")
    await db.execute(
        pg_insert(note_list_taglists).values(note_list_id=note_list.id, tag_list_id=tag_list_id).on_conflict_do_nothing()
    )
    await db.commit()
    return None


@router.delete("/{note_list_id}/taglists/{tag_list_id}", status_code=204)
async def detach_taglist_from_note_list(
    note_list_id: uuid.UUID,
    tag_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_list = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    await db.execute(
        note_list_taglists.delete().where(
            note_list_taglists.c.note_list_id == note_list.id,
            note_list_taglists.c.tag_list_id == tag_list_id,
        )
    )
    await db.commit()
    return None


async def _get_effective_taglist_ids_for_note_list(db: AsyncSession, owner_id: uuid.UUID, note_list_id: uuid.UUID) -> set[uuid.UUID]:
    # Union of taglists from this list up its ancestors
    # Validate starting list ownership
    await _get_owned_note_list_or_404(db, owner_id, note_list_id)
    effective: set[uuid.UUID] = set()
    current_id = note_list_id
    while current_id is not None:
        # fetch taglists for current level
        res = await db.execute(
            select(note_list_taglists.c.tag_list_id)
            .where(note_list_taglists.c.note_list_id == current_id)
        )
        effective.update([row for row in res.scalars().all()])
        # move to parent
        parent_res = await db.execute(select(NoteList.parent_list_id).where(NoteList.id == current_id))
        current_id = parent_res.scalar_one_or_none()
    return effective


@router.get("/{note_list_id}/effective-taglists", response_model=list[TagListOut])
async def get_effective_taglists_for_note_list(
    note_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ids = await _get_effective_taglist_ids_for_note_list(db, current_user.id, note_list_id)
    if not ids:
        return []
    res = await db.execute(select(TagList).where(TagList.owner_id == current_user.id, TagList.id.in_(list(ids))))
    return res.scalars().all()


@router.get("/{note_list_id}/available-tags", response_model=list[TagOut])
async def get_available_tags_for_note_list(
    note_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ids = await _get_effective_taglist_ids_for_note_list(db, current_user.id, note_list_id)
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


@router.post("/{note_list_id}/tags/{tag_id}", status_code=204)
async def attach_tag_to_note_list(
    note_list_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_list = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    await _get_owned_tag_or_404(db, current_user.id, tag_id)
    await db.execute(pg_insert(note_list_tags).values(note_list_id=note_list.id, tag_id=tag_id).on_conflict_do_nothing())
    await db.commit()
    return None


@router.delete("/{note_list_id}/tags/{tag_id}", status_code=204)
async def detach_tag_from_note_list(
    note_list_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_list = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    await _get_owned_tag_or_404(db, current_user.id, tag_id)
    await db.execute(note_list_tags.delete().where(note_list_tags.c.note_list_id == note_list.id, note_list_tags.c.tag_id == tag_id))
    await db.commit()
    return None




# Hierarchy Management Endpoints

@router.get("/{note_list_id}/children", response_model=list[NoteListOut])
async def get_note_list_children(
    note_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    res = await db.execute(
        select(NoteList).where(NoteList.parent_list_id == note_list_id).order_by(NoteList.sort_order, NoteList.created_at)
    )
    return res.scalars().all()


@router.post("/{note_list_id}/children", response_model=NoteListOut, status_code=201)
async def create_child_note_list(
    note_list_id: uuid.UUID,
    payload: NoteListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parent_list = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    
    child_list = NoteList(
        owner_id=current_user.id,
        parent_list_id=note_list_id,
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


async def _check_circular_reference_note_list(db: AsyncSession, note_list_id: uuid.UUID, parent_id: uuid.UUID) -> None:
    current_parent_id = parent_id
    visited = {note_list_id}
    
    while current_parent_id:
        if current_parent_id in visited:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="circular_reference_detected"
            )
        visited.add(current_parent_id)
        
        res = await db.execute(select(NoteList.parent_list_id).where(NoteList.id == current_parent_id))
        current_parent_id = res.scalar_one_or_none()


@router.patch("/{note_list_id}/parent", response_model=NoteListOut)
async def update_note_list_parent(
    note_list_id: uuid.UUID,
    payload: NoteListParentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_list = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    
    if payload.parent_list_id:
        await _get_owned_note_list_or_404(db, current_user.id, payload.parent_list_id)
        await _check_circular_reference_note_list(db, note_list_id, payload.parent_list_id)
        note_list.parent_list_id = payload.parent_list_id
    else:
        root = await _get_or_create_system_root(db, current_user.id)
        note_list.parent_list_id = root.id
    await db.commit()
    await db.refresh(note_list)
    root = await _get_or_create_system_root(db, current_user.id)
    return NoteListOut(
        id=note_list.id,
        owner_id=note_list.owner_id,
        parent_list_id=(None if note_list.parent_list_id == root.id else note_list.parent_list_id),
        name=note_list.name,
        description=note_list.description,
        sort_order=note_list.sort_order,
        created_at=note_list.created_at,
        updated_at=note_list.updated_at,
    )


@router.post("/{note_list_id}/default", status_code=204)
async def set_default_note_list(
    note_list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    nl = await _get_owned_note_list_or_404(db, current_user.id, note_list_id)
    await db.execute(
        pg_insert(DefaultNoteList.__table__).values(user_id=current_user.id, note_list_id=nl.id).on_conflict_do_update(
            index_elements=[DefaultNoteList.__table__.c.user_id],
            set_={"note_list_id": nl.id},
        )
    )
    await db.commit()
    return None
