from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
import logging

from app.db.deps import get_db
from app.api.auth import get_current_user
from app.models.user import User  
from app.models.node import Node
from app.models.default_node import DefaultNode

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/default-node")
async def get_default_node(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the current user's default node"""
    try:
        logger.info(f"Getting default node for user {current_user.id}")
        stmt = select(DefaultNode).where(DefaultNode.owner_id == current_user.id)
        result = await db.execute(stmt)
        default_node = result.scalar_one_or_none()
        
        if default_node:
            logger.info(f"Found default node: {default_node.node_id}")
            return {"node_id": str(default_node.node_id)}
        else:
            logger.info("No default node found")
            return {"node_id": None}
    except Exception as e:
        logger.error(f"Error getting default node: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get default node: {str(e)}")


@router.put("/default-node")
async def set_default_node(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set the user's default node"""
    try:
        logger.info(f"Setting default node for user {current_user.id}, request: {request}")
        node_id_str = request.get("node_id")
        
        # Validate node exists and belongs to user if provided
        if node_id_str:
            try:
                node_uuid = uuid.UUID(node_id_str)
                logger.info(f"Parsed node UUID: {node_uuid}")
            except ValueError as ve:
                logger.error(f"Invalid UUID format: {node_id_str}")
                raise HTTPException(status_code=400, detail="Invalid node ID format")
            
            # Check if node exists and belongs to user
            stmt = select(Node).where(
                Node.id == node_uuid,
                Node.owner_id == current_user.id
            )
            result = await db.execute(stmt)
            node = result.scalar_one_or_none()
            
            if not node:
                logger.error(f"Node not found: {node_uuid} for user {current_user.id}")
                raise HTTPException(status_code=404, detail="Node not found")
        
        # Check if user already has a default node record
        stmt = select(DefaultNode).where(DefaultNode.owner_id == current_user.id)
        result = await db.execute(stmt)
        existing_default = result.scalar_one_or_none()
        logger.info(f"Existing default: {existing_default}")
        
        if node_id_str:
            if existing_default:
                # Update existing record
                logger.info("Updating existing default")
                existing_default.node_id = node_uuid
            else:
                # Create new record
                logger.info("Creating new default")
                new_default = DefaultNode(
                    owner_id=current_user.id,
                    node_id=node_uuid
                )
                db.add(new_default)
        else:
            # Remove default node (set to None)
            if existing_default:
                logger.info("Deleting existing default")
                await db.delete(existing_default)
        
        await db.commit()
        logger.info("Default node saved successfully")
        
        return {"success": True, "node_id": node_id_str}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting default node: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to set default node: {str(e)}")