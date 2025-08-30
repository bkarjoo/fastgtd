from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy.exc import IntegrityError

from app.db.deps import get_db
from app.api.auth import get_current_user
from app.models.tag import Tag
from app.models.user import User


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
    name: str = Query(..., description="Tag name"),
    description: Optional[str] = Query(None, description="Tag description"),
    color: Optional[str] = Query(None, description="Hex color code (e.g., #FF0000)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new tag or return existing one if it already exists"""
    
    # Check if tag already exists
    existing_query = select(Tag).where(
        Tag.owner_id == current_user.id,
        Tag.name == name
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
    
    # Validate color format if provided
    if color and not color.startswith('#'):
        raise HTTPException(status_code=400, detail="Color must be a hex code starting with #")
    
    # Create new tag
    try:
        tag = Tag(
            owner_id=current_user.id,
            name=name.strip(),
            description=description.strip() if description else None,
            color=color
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
    
    query = select(Tag).where(
        Tag.id == tag_id,
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
    name: Optional[str] = Query(None, description="New tag name"),
    description: Optional[str] = Query(None, description="New tag description"),
    color: Optional[str] = Query(None, description="New hex color code"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing tag"""
    
    # Get existing tag
    query = select(Tag).where(
        Tag.id == tag_id,
        Tag.owner_id == current_user.id
    )
    result = await db.execute(query)
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Update fields if provided
    try:
        if name is not None:
            # Check for duplicate name (excluding current tag)
            dup_query = select(Tag).where(
                Tag.owner_id == current_user.id,
                Tag.name == name.strip(),
                Tag.id != tag_id
            )
            dup_result = await db.execute(dup_query)
            if dup_result.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="Tag with this name already exists")
            
            tag.name = name.strip()
        
        if description is not None:
            tag.description = description.strip() if description else None
            
        if color is not None:
            if color and not color.startswith('#'):
                raise HTTPException(status_code=400, detail="Color must be a hex code starting with #")
            tag.color = color
        
        await db.commit()
        await db.refresh(tag)
        
        return {
            "id": str(tag.id),
            "name": tag.name,
            "description": tag.description,
            "color": tag.color,
            "updated_at": tag.updated_at.isoformat() if tag.updated_at else None
        }
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Tag with this name already exists")


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a tag and all its node associations"""
    
    # Get existing tag
    query = select(Tag).where(
        Tag.id == tag_id,
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