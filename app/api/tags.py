from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy.exc import IntegrityError

from app.db.deps import get_db
from app.api.auth import get_current_user
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagUpdate


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=List[dict])
async def list_tags(
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(50, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all tags for the current user with optional search filtering"""
    
    query = select(Tag).where(Tag.owner_id == current_user.id)
    
    if q:
        query = query.where(Tag.name.ilike(f"%{q}%"))
    
    query = query.order_by(Tag.name).limit(limit).offset(offset)
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    return [
        {
            "id": str(tag.id),
            "name": tag.name,
            "description": tag.description,
            "color": tag.color,
            "created_at": tag.created_at.isoformat() if tag.created_at else None
        }
        for tag in tags
    ]


@router.post("", status_code=201)
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new tag or return existing one if it already exists"""

    # Check if tag already exists
    existing_query = select(Tag).where(
        Tag.owner_id == current_user.id,
        Tag.name == tag_data.name
    )
    result = await db.execute(existing_query)
    existing_tag = result.scalar_one_or_none()

    if existing_tag:
        return {
            "id": str(existing_tag.id),
            "name": existing_tag.name,
            "description": existing_tag.description,
            "color": existing_tag.color,
            "created_at": existing_tag.created_at.isoformat() if existing_tag.created_at else None,
            "existed": True
        }

    # Create new tag (color validation already done by Pydantic)
    try:
        tag = Tag(
            owner_id=current_user.id,
            name=tag_data.name.strip(),
            description=tag_data.description.strip() if tag_data.description else None,
            color=tag_data.color
        )
        db.add(tag)
        await db.commit()
        await db.refresh(tag)

        return {
            "id": str(tag.id),
            "name": tag.name,
            "description": tag.description,
            "color": tag.color,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
            "existed": False
        }
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Tag with this name already exists"
        )


@router.get("/search")
async def search_tags(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search tags by name for autocomplete functionality"""
    
    # Search for tags starting with the query (for autocomplete)
    query = select(Tag).where(
        Tag.owner_id == current_user.id,
        Tag.name.ilike(f"{q}%")
    ).order_by(Tag.name).limit(limit)
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    return [
        {
            "id": str(tag.id),
            "name": tag.name,
            "description": tag.description,
            "color": tag.color
        }
        for tag in tags
    ]


@router.get("/{tag_id}")
async def get_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific tag by ID"""

    try:
        from uuid import UUID
        tag_uuid = UUID(tag_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    query = select(Tag).where(
        Tag.id == tag_uuid,
        Tag.owner_id == current_user.id
    )
    result = await db.execute(query)
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return {
        "id": str(tag.id),
        "name": tag.name,
        "description": tag.description,
        "color": tag.color,
        "created_at": tag.created_at.isoformat() if tag.created_at else None,
        "updated_at": tag.updated_at.isoformat() if tag.updated_at else None
    }


@router.put("/{tag_id}")
async def update_tag(
    tag_id: str,
    tag_data: TagUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing tag. If renaming to an existing tag name, merges the tags."""
    from app.models.node_associations import node_tags
    from sqlalchemy import insert, delete as sql_delete

    try:
        from uuid import UUID
        tag_uuid = UUID(tag_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Get existing tag
    query = select(Tag).where(
        Tag.id == tag_uuid,
        Tag.owner_id == current_user.id
    )
    result = await db.execute(query)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Handle tag name update with potential merge
    if tag_data.name is not None and tag_data.name.strip() != tag.name:
        new_name = tag_data.name.strip()
        
        # Check if a tag with the new name already exists
        existing_query = select(Tag).where(
            Tag.owner_id == current_user.id,
            Tag.name == new_name,
            Tag.id != tag_uuid
        )
        existing_result = await db.execute(existing_query)
        existing_tag = existing_result.scalar_one_or_none()
        
        if existing_tag:
            # Merge tags: move all node associations from current tag to existing tag
            
            # Get all nodes tagged with the current tag
            current_associations_query = select(node_tags.c.node_id).where(
                node_tags.c.tag_id == tag.id
            )
            current_result = await db.execute(current_associations_query)
            current_node_ids = [row[0] for row in current_result.fetchall()]
            
            if current_node_ids:
                # Get nodes already tagged with the existing tag to avoid duplicates
                existing_associations_query = select(node_tags.c.node_id).where(
                    node_tags.c.tag_id == existing_tag.id,
                    node_tags.c.node_id.in_(current_node_ids)
                )
                existing_result = await db.execute(existing_associations_query)
                existing_node_ids = {row[0] for row in existing_result.fetchall()}
                
                # Find nodes that need to be moved (not already associated with existing tag)
                nodes_to_move = [node_id for node_id in current_node_ids if node_id not in existing_node_ids]
                
                if nodes_to_move:
                    # Add associations to the existing tag
                    associations_to_add = [
                        {"node_id": node_id, "tag_id": existing_tag.id}
                        for node_id in nodes_to_move
                    ]
                    await db.execute(insert(node_tags).values(associations_to_add))
                
                # Delete all associations with the current tag
                await db.execute(
                    sql_delete(node_tags).where(node_tags.c.tag_id == tag.id)
                )
            
            # Delete the current tag
            await db.delete(tag)
            await db.commit()
            
            return {
                "id": str(existing_tag.id),
                "name": existing_tag.name,
                "description": existing_tag.description,
                "color": existing_tag.color,
                "merged": True,
                "message": f"Tag merged with existing tag '{new_name}'"
            }
        else:
            # No existing tag with new name, just rename
            tag.name = new_name
    
    # Update other fields (color validation already done by Pydantic)
    if tag_data.description is not None:
        tag.description = tag_data.description.strip() if tag_data.description else None

    if tag_data.color is not None:
        tag.color = tag_data.color
    
    await db.commit()
    await db.refresh(tag)
    
    return {
        "id": str(tag.id),
        "name": tag.name,
        "description": tag.description,
        "color": tag.color,
        "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
        "merged": False
    }


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a tag and all its node associations"""

    try:
        from uuid import UUID
        tag_uuid = UUID(tag_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Get existing tag
    query = select(Tag).where(
        Tag.id == tag_uuid,
        Tag.owner_id == current_user.id
    )
    result = await db.execute(query)
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Delete tag (cascade will handle node associations via foreign key)
    await db.delete(tag)
    await db.commit()
    
    return None