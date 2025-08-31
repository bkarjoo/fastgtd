"""Rules API endpoints."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.api.auth import get_current_user
from app.models.user import User
from app.models.rule import Rule
from app.schemas.rule import (
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    RuleListResponse
)

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/", response_model=RuleListResponse)
async def get_rules(
    include_public: bool = False,
    include_system: bool = False,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all rules accessible to the current user."""
    conditions = [Rule.owner_id == current_user.id]
    
    if include_public:
        conditions.append(Rule.is_public == True)
    
    if include_system:
        conditions.append(Rule.is_system == True)
    
    # Build query with OR if we have multiple conditions
    if len(conditions) > 1:
        query = select(Rule).where(or_(*conditions))
    else:
        query = select(Rule).where(conditions[0])
    
    result = await session.execute(query.order_by(Rule.created_at.desc()))
    rules = result.scalars().all()
    
    return RuleListResponse(
        rules=[RuleResponse.from_orm(rule) for rule in rules],
        total=len(rules)
    )


@router.post("/", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: RuleCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new rule."""
    rule = Rule(
        owner_id=current_user.id,
        name=rule_data.name,
        description=rule_data.description,
        rule_data=rule_data.rule_data,
        is_public=rule_data.is_public,
        is_system=False  # Users cannot create system rules
    )
    
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    
    return RuleResponse.from_orm(rule)


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific rule."""
    query = select(Rule).where(
        Rule.id == rule_id,
        or_(
            Rule.owner_id == current_user.id,
            Rule.is_public == True,
            Rule.is_system == True
        )
    )
    
    result = await session.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found or access denied"
        )
    
    return RuleResponse.from_orm(rule)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    rule_update: RuleUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a rule."""
    query = select(Rule).where(
        Rule.id == rule_id,
        Rule.owner_id == current_user.id,
        Rule.is_system == False  # Cannot edit system rules
    )
    
    result = await session.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found or cannot be edited"
        )
    
    # Update fields
    if rule_update.name is not None:
        rule.name = rule_update.name
    if rule_update.description is not None:
        rule.description = rule_update.description
    if rule_update.rule_data is not None:
        rule.rule_data = rule_update.rule_data
    if rule_update.is_public is not None:
        rule.is_public = rule_update.is_public
    
    await session.commit()
    await session.refresh(rule)
    
    return RuleResponse.from_orm(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a rule."""
    query = select(Rule).where(
        Rule.id == rule_id,
        Rule.owner_id == current_user.id,
        Rule.is_system == False  # Cannot delete system rules
    )
    
    result = await session.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found or cannot be deleted"
        )
    
    await session.delete(rule)
    await session.commit()


@router.post("/{rule_id}/duplicate", response_model=RuleResponse)
async def duplicate_rule(
    rule_id: UUID,
    new_name: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Duplicate an existing rule."""
    # Find the original rule
    query = select(Rule).where(
        Rule.id == rule_id,
        or_(
            Rule.owner_id == current_user.id,
            Rule.is_public == True,
            Rule.is_system == True
        )
    )
    
    result = await session.execute(query)
    original_rule = result.scalar_one_or_none()
    
    if not original_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found or access denied"
        )
    
    # Create duplicate
    duplicate = Rule(
        owner_id=current_user.id,
        name=new_name or f"{original_rule.name} (Copy)",
        description=original_rule.description,
        rule_data=original_rule.rule_data,
        is_public=False,  # Duplicates are private by default
        is_system=False   # Users cannot create system rules
    )
    
    session.add(duplicate)
    await session.commit()
    await session.refresh(duplicate)
    
    return RuleResponse.from_orm(duplicate)