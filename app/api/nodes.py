from typing import List, Optional, Union
from uuid import UUID
import os
import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.db.deps import get_db
from app.models.user import User
from app.models.node import Node, Task, Note, SmartFolder, Template, Folder
from app.models.tag import Tag, node_tags
from app.schemas.node import (
    NodeCreate, NodeUpdate, NodeResponse, TaskCreate, TaskUpdate, TaskResponse,
    NoteCreate, NoteUpdate, NoteResponse, FolderCreate, FolderUpdate, FolderResponse,
    SmartFolderCreate, SmartFolderUpdate, SmartFolderResponse, 
    TemplateCreate, TemplateUpdate, TemplateResponse,
    NodeResponseUnion, NodeFilter, NodeTree, NodeTreeItem, 
    NodeMove, NodeReorder, create_node_response
)
from app.schemas.tag import TagResponse
from app.api.auth import get_current_user
from app.services.smart_folder_engine import SmartFolderRulesEngine

router = APIRouter(prefix="/nodes", tags=["nodes"])


# Template-specific endpoints (must come before /{node_id} routes)
@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """List all templates for the current user"""
    
    query = select(Template).where(Template.owner_id == current_user.id)
    
    if category:
        query = query.where(Template.category == category)
    
    query = query.order_by(Template.title).limit(limit).offset(offset)
    result = await session.execute(query)
    templates = result.scalars().all()
    
    responses = []
    for template in templates:
        response = await convert_node_to_response(template, session)
        responses.append(response)
    
    return responses


@router.post("/templates/{template_id}/instantiate", response_model=NodeResponseUnion)
async def instantiate_template(
    template_id: UUID,
    name: str,
    parent_id: Optional[UUID] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a copy of a template with all its contents"""
    
    # Get the template
    template_query = select(Template).where(
        Template.id == template_id,
        Template.owner_id == current_user.id
    )
    result = await session.execute(template_query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get template children
    children_query = select(Node).where(Node.parent_id == template_id)
    children_result = await session.execute(children_query)
    children = children_result.scalars().all()
    
    if not children:
        raise HTTPException(status_code=400, detail="Template has no content to instantiate")
    
    # Determine target location: use template's target_node_id if set, otherwise use parent_id parameter
    target_parent_id = template.target_node_id if template.target_node_id else parent_id
    
    # Validate target parent exists if specified
    if target_parent_id:
        parent_query = select(Node).where(
            Node.id == target_parent_id,
            Node.owner_id == current_user.id
        )
        parent_result = await session.execute(parent_query)
        parent_node = parent_result.scalar_one_or_none()
        if not parent_node:
            raise HTTPException(status_code=404, detail="Target parent node not found")
    
    # Handle create_container setting
    if template.create_container:
        # Create wrapper folder and copy contents inside
        root_folder = Folder(
            owner_id=current_user.id,
            parent_id=target_parent_id,
            title=name,
            sort_order=0
        )
        session.add(root_folder)
        await session.flush()  # Get ID without committing
        
        # Copy children under the wrapper folder
        for child in children:
            await _copy_node_hierarchy(child, root_folder.id, session)
        
        # Update template usage count
        template.usage_count += 1
        await session.commit()
        
        # Return the wrapper folder
        await session.refresh(root_folder)
        return await convert_node_to_response(root_folder, session)
    
    else:
        # Copy contents directly to target location (no wrapper folder)
        copied_nodes = []
        for child in children:
            copied_node = await _copy_node_hierarchy(child, target_parent_id, session, name_override=None)
            copied_nodes.append(copied_node)
        
        # Update template usage count
        template.usage_count += 1
        await session.commit()
        
        # Return the first copied node (or could return all of them)
        if copied_nodes:
            await session.refresh(copied_nodes[0])
            return await convert_node_to_response(copied_nodes[0], session)
        else:
            raise HTTPException(status_code=500, detail="Failed to copy template contents")




# CRUD Operations
@router.post("/", response_model=NodeResponseUnion)
async def create_node(
    node_data: Union[TaskCreate, NoteCreate, FolderCreate, SmartFolderCreate, TemplateCreate],
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NodeResponseUnion:
    """Create a new node (task, note, folder, smart folder, or template)"""
    
    # Create type-specific node directly (polymorphic)
    if node_data.node_type == "task":
        task_data = node_data.task_data
        node = Task(
            owner_id=current_user.id,
            parent_id=node_data.parent_id,
            title=node_data.title,
            sort_order=node_data.sort_order,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            due_at=task_data.due_at,
            earliest_start_at=task_data.earliest_start_at,
            completed_at=task_data.completed_at,
            archived=task_data.archived,
            recurrence_rule=task_data.recurrence_rule,
            recurrence_anchor=task_data.recurrence_anchor
        )
        
    elif node_data.node_type == "note":
        note_data = node_data.note_data
        node = Note(
            owner_id=current_user.id,
            parent_id=node_data.parent_id,
            title=node_data.title,
            sort_order=node_data.sort_order,
            body=note_data.body
        )
    elif node_data.node_type == "folder":
        # Folder with optional description
        folder_data = node_data.folder_data if hasattr(node_data, 'folder_data') and node_data.folder_data else None
        node = Folder(
            owner_id=current_user.id,
            parent_id=node_data.parent_id,
            title=node_data.title,
            sort_order=node_data.sort_order,
            description=folder_data.description if folder_data else None
        )
    elif node_data.node_type == "smart_folder":
        smart_folder_data = node_data.smart_folder_data
        
        # Validate rules before creation (only if rules exist)
        if smart_folder_data.rules is not None:
            rules_engine = SmartFolderRulesEngine(session)
            # Handle both dict and Pydantic model cases
            rules_data = smart_folder_data.rules.model_dump() if hasattr(smart_folder_data.rules, 'model_dump') else smart_folder_data.rules
            validation_errors = rules_engine.validate_rules(rules_data)
            if validation_errors:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid rules: {'; '.join(validation_errors)}"
                )
        
        node = SmartFolder(
            owner_id=current_user.id,
            parent_id=node_data.parent_id,
            title=node_data.title,
            sort_order=node_data.sort_order,
            rules=smart_folder_data.rules or {"conditions": [], "logic": "AND"},
            auto_refresh=smart_folder_data.auto_refresh,
            description=smart_folder_data.description
        )
    elif node_data.node_type == "template":
        template_data = node_data.template_data
        node = Template(
            owner_id=current_user.id,
            parent_id=node_data.parent_id,
            title=node_data.title,
            sort_order=node_data.sort_order,
            description=template_data.description,
            category=template_data.category,
            usage_count=template_data.usage_count,
            target_node_id=template_data.target_node_id,
            create_container=template_data.create_container
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid node_type")
    
    session.add(node)
    await session.commit()
    await session.refresh(node)
    
    return await convert_node_to_response(node, session)


@router.get("/{node_id}", response_model=NodeResponseUnion)
async def get_node(
    node_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NodeResponseUnion:
    """Get a specific node by ID"""
    return await get_node_by_id(node_id, session, current_user)


@router.put("/{node_id}", response_model=NodeResponseUnion)
async def update_node(
    node_id: UUID,
    node_data: Union[TaskUpdate, NoteUpdate, FolderUpdate, SmartFolderUpdate, TemplateUpdate],
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NodeResponseUnion:
    """Update a node"""
    
    # Get the node
    node = await get_node_by_id_raw(node_id, session, current_user)
    
    # Update base node fields
    if node_data.title is not None:
        node.title = node_data.title
    # Check if parent_id was explicitly provided (even if it's None/null)
    # Use model_fields_set to check if parent_id was explicitly provided in the request
    if 'parent_id' in node_data.model_fields_set:
        node.parent_id = node_data.parent_id
    if node_data.sort_order is not None:
        node.sort_order = node_data.sort_order
    
    # Update type-specific data
    if isinstance(node_data, TaskUpdate) and node_data.task_data and isinstance(node, Task):
        task_data = node_data.task_data
        if task_data.description is not None:
            node.description = task_data.description
        if task_data.status is not None:
            node.status = task_data.status
        if task_data.priority is not None:
            node.priority = task_data.priority
        if task_data.due_at is not None:
            node.due_at = task_data.due_at
        if task_data.earliest_start_at is not None:
            node.earliest_start_at = task_data.earliest_start_at
        if task_data.completed_at is not None:
            node.completed_at = task_data.completed_at
        if task_data.archived is not None:
            node.archived = task_data.archived
        if task_data.recurrence_rule is not None:
            node.recurrence_rule = task_data.recurrence_rule
        if task_data.recurrence_anchor is not None:
            node.recurrence_anchor = task_data.recurrence_anchor
            
    elif isinstance(node_data, NoteUpdate) and node_data.note_data and isinstance(node, Note):
        note_data = node_data.note_data
        if note_data.body is not None:
            node.body = note_data.body
            
    elif isinstance(node_data, SmartFolderUpdate) and node_data.smart_folder_data and isinstance(node, SmartFolder):
        smart_folder_data = node_data.smart_folder_data
        
        # Handle rule_id update (new methodology)
        if smart_folder_data.rule_id is not None:
            # Validate that the rule exists and is accessible
            from app.models.rule import Rule
            rule_query = select(Rule).where(
                Rule.id == smart_folder_data.rule_id,
                or_(
                    Rule.owner_id == current_user.id,
                    Rule.is_public == True,
                    Rule.is_system == True
                )
            )
            rule_result = await session.execute(rule_query)
            rule = rule_result.scalar_one_or_none()
            if not rule:
                raise HTTPException(
                    status_code=404,
                    detail=f"Rule {smart_folder_data.rule_id} not found or not accessible"
                )
            node.rule_id = smart_folder_data.rule_id
            
        # Handle legacy rules update (deprecated but kept for backward compatibility)
        if smart_folder_data.rules is not None:
            # Validate rules if provided
            from app.services.smart_folder_engine import SmartFolderRulesEngine
            rules_engine = SmartFolderRulesEngine(session)
            validation_errors = rules_engine.validate_rules(smart_folder_data.rules)
            if validation_errors:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid rules: {'; '.join(validation_errors)}"
                )
            node.rules = smart_folder_data.rules
            
        if smart_folder_data.auto_refresh is not None:
            node.auto_refresh = smart_folder_data.auto_refresh
        if smart_folder_data.description is not None:
            node.description = smart_folder_data.description
            
    elif isinstance(node_data, FolderUpdate) and node_data.folder_data and isinstance(node, Folder):
        folder_data = node_data.folder_data
        if folder_data.description is not None:
            node.description = folder_data.description

    elif isinstance(node_data, TemplateUpdate) and node_data.template_data and isinstance(node, Template):
        template_data = node_data.template_data
        if template_data.description is not None:
            node.description = template_data.description
        if template_data.category is not None:
            node.category = template_data.category
        if template_data.usage_count is not None:
            node.usage_count = template_data.usage_count
        if template_data.target_node_id is not None:
            node.target_node_id = template_data.target_node_id
        if template_data.create_container is not None:
            node.create_container = template_data.create_container
    
    await session.commit()
    return await get_node_by_id(node_id, session, current_user)


@router.delete("/{node_id}")
async def delete_node(
    node_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a node and all its children"""
    from app.models.artifact import Artifact
    
    node = await get_node_by_id_raw(node_id, session, current_user)
    
    # Get all artifacts associated with this node before deletion
    artifacts_result = await session.execute(
        select(Artifact).filter(Artifact.node_id == node_id)
    )
    artifacts = artifacts_result.scalars().all()
    
    # Delete artifact files from filesystem
    for artifact in artifacts:
        file_path = Path(artifact.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass  # Continue even if file deletion fails
    
    # Delete node (this will cascade delete artifacts from database)
    await session.delete(node)
    await session.commit()
    
    return {"message": "Node deleted successfully"}


# Hierarchy Operations
@router.get("/", response_model=List[NodeResponseUnion])
async def list_nodes(
    filter_params: NodeFilter = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[NodeResponseUnion]:
    """List nodes with filtering and pagination"""
    
    # Build base query (include all node types including templates)
    query = select(Node).where(Node.owner_id == current_user.id)
    
    # Apply filters
    if filter_params.node_type:
        query = query.where(Node.node_type == filter_params.node_type)
    
    if filter_params.parent_id is not None:
        query = query.where(Node.parent_id == filter_params.parent_id)
    
    if filter_params.search:
        search_term = f"%{filter_params.search}%"
        query = query.where(Node.title.ilike(search_term))
    
    # Add joins for type-specific filtering
    if filter_params.status or filter_params.priority or filter_params.archived is not None:
        query = query.join(Task).where(
            and_(
                filter_params.status is None or Task.status == filter_params.status,
                filter_params.priority is None or Task.priority == filter_params.priority,
                filter_params.archived is None or Task.archived == filter_params.archived
            )
        )
    
    # Apply pagination
    query = query.offset(filter_params.offset).limit(filter_params.limit)
    query = query.order_by(Node.sort_order, Node.created_at)
    
    result = await session.execute(query)
    nodes = result.scalars().all()
    
    # Convert to response format
    responses = []
    for node in nodes:
        response = await convert_node_to_response(node, session)
        responses.append(response)
    
    return responses


@router.get("/tree/{root_id}", response_model=NodeTree)
async def get_node_tree(
    root_id: Optional[UUID] = None,
    max_depth: int = Query(default=10, le=20),
    expanded_ids: List[UUID] = Query(default=[]),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NodeTree:
    """Get node tree structure"""
    
    # Build recursive query to get tree structure
    tree_items = await build_node_tree(root_id, max_depth, expanded_ids, session, current_user)
    
    return NodeTree(
        root_id=root_id,
        items=tree_items,
        total_count=len(tree_items)
    )


@router.post("/move")
async def move_node(
    move_data: NodeMove,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Move a node to a new parent/position"""
    
    node = await get_node_by_id_raw(move_data.node_id, session, current_user)
    
    # Validate move (prevent circular references)
    if move_data.new_parent_id:
        await validate_move(move_data.node_id, move_data.new_parent_id, session, current_user)
    
    node.parent_id = move_data.new_parent_id
    if move_data.new_sort_order is not None:
        node.sort_order = move_data.new_sort_order
    
    await session.commit()
    return {"message": "Node moved successfully"}


@router.post("/reorder")
async def reorder_nodes(
    reorder_data: NodeReorder,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reorder nodes within the same parent"""
    
    # Update sort orders
    for i, node_id in enumerate(reorder_data.node_ids):
        query = (
            select(Node)
            .where(Node.id == node_id)
            .where(Node.owner_id == current_user.id)
        )
        result = await session.execute(query)
        node = result.scalar_one_or_none()
        
        if node:
            node.sort_order = i
    
    await session.commit()
    return {"message": "Nodes reordered successfully"}


# Helper functions
async def get_node_by_id_raw(
    node_id: UUID, 
    session: AsyncSession, 
    current_user: User
) -> Node:
    """Get raw node object with ownership check"""
    query = (
        select(Node)
        .where(Node.id == node_id)
        .where(Node.owner_id == current_user.id)
    )
    result = await session.execute(query)
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return node


async def get_node_by_id(
    node_id: UUID, 
    session: AsyncSession, 
    current_user: User
) -> NodeResponseUnion:
    """Get node with full response format"""
    node = await get_node_by_id_raw(node_id, session, current_user)
    return await convert_node_to_response(node, session)


async def convert_node_to_response(node: Node, session: AsyncSession) -> NodeResponseUnion:
    """Convert node to appropriate response format"""
    
    # Get children count
    children_query = select(func.count(Node.id)).where(Node.parent_id == node.id)
    children_result = await session.execute(children_query)
    children_count = children_result.scalar() or 0
    
    # Load tags for the node
    tags_query = select(Tag).join(node_tags).where(node_tags.c.node_id == node.id)
    tags_result = await session.execute(tags_query)
    tags = tags_result.scalars().all()
    
    # Convert tags to response format
    tag_responses = [
        TagResponse(
            id=tag.id,
            name=tag.name,
            description=tag.description,
            color=tag.color,
            created_at=tag.created_at
        )
        for tag in tags
    ]
    
    base_data = {
        "id": node.id,
        "owner_id": node.owner_id,
        "parent_id": node.parent_id,
        "node_type": node.node_type,
        "title": node.title,
        "sort_order": node.sort_order,
        "created_at": node.created_at,
        "updated_at": node.updated_at,
        "is_list": children_count > 0,
        "children_count": children_count,
        "tags": tag_responses
    }
    
    if node.node_type == "task":
        # Get task-specific data
        task_query = select(Task).where(Task.id == node.id)
        task_result = await session.execute(task_query)
        task = task_result.scalar_one()
        
        return TaskResponse(
            **base_data,
            task_data={
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "due_at": task.due_at,
                "earliest_start_at": task.earliest_start_at,
                "completed_at": task.completed_at,
                "archived": task.archived,
                "recurrence_rule": task.recurrence_rule,
                "recurrence_anchor": task.recurrence_anchor
            }
        )
    
    elif node.node_type == "note":
        # Get note-specific data
        note_query = select(Note).where(Note.id == node.id)
        note_result = await session.execute(note_query)
        note = note_result.scalar_one()
        
        return NoteResponse(
            **base_data,
            note_data={
                "body": note.body
            }
        )
    
    elif node.node_type == "smart_folder":
        # Get smart folder-specific data
        smart_folder_query = select(SmartFolder).where(SmartFolder.id == node.id)
        smart_folder_result = await session.execute(smart_folder_query)
        smart_folder = smart_folder_result.scalar_one()
        
        return SmartFolderResponse(
            **base_data,
            smart_folder_data={
                "rule_id": smart_folder.rule_id,
                "rules": smart_folder.rules,
                "auto_refresh": smart_folder.auto_refresh,
                "description": smart_folder.description
            }
        )
    
    elif node.node_type == "template":
        # Get template-specific data
        template_query = select(Template).where(Template.id == node.id)
        template_result = await session.execute(template_query)
        template = template_result.scalar_one()
        
        return TemplateResponse(
            **base_data,
            template_data={
                "description": template.description,
                "category": template.category,
                "usage_count": template.usage_count,
                "target_node_id": template.target_node_id,
                "create_container": template.create_container
            }
        )
    
    elif node.node_type == "folder":
        # Get folder-specific data
        folder_query = select(Folder).where(Folder.id == node.id)
        folder_result = await session.execute(folder_query)
        folder = folder_result.scalar_one_or_none()

        if folder:
            return FolderResponse(
                **base_data,
                folder_data={
                    "description": folder.description
                } if folder.description else None
            )
        else:
            # Fallback for folders without description
            return FolderResponse(**base_data)
    
    else:
        raise ValueError(f"Unknown node type: {node.node_type}")


async def build_node_tree(
    root_id: Optional[UUID],
    max_depth: int,
    expanded_ids: List[UUID],
    session: AsyncSession,
    current_user: User
) -> List[NodeTreeItem]:
    """Build hierarchical tree structure"""
    
    # This is a simplified version - would need more complex recursive logic
    # For now, just return flat list of children
    query = (
        select(Node)
        .where(Node.owner_id == current_user.id)
        .where(Node.parent_id == root_id)
        .order_by(Node.sort_order, Node.created_at)
    )
    
    result = await session.execute(query)
    nodes = result.scalars().all()
    
    tree_items = []
    for node in nodes:
        # Get children count
        children_query = select(func.count(Node.id)).where(Node.parent_id == node.id)
        children_result = await session.execute(children_query)
        children_count = children_result.scalar() or 0
        
        tree_items.append(NodeTreeItem(
            id=node.id,
            title=node.title,
            node_type=node.node_type,
            parent_id=node.parent_id,
            sort_order=node.sort_order,
            is_list=children_count > 0,
            children_count=children_count,
            level=0,  # Would calculate based on depth
            expanded=node.id in expanded_ids
        ))
    
    return tree_items


async def validate_move(
    node_id: UUID,
    new_parent_id: UUID,
    session: AsyncSession,
    current_user: User
):
    """Validate that move doesn't create circular reference"""
    
    # Check if new_parent_id is a descendant of node_id
    current_parent = new_parent_id
    while current_parent:
        if current_parent == node_id:
            raise HTTPException(
                status_code=400, 
                detail="Cannot move node to be a child of itself or its descendants"
            )
        
        # Get parent of current_parent
        query = (
            select(Node.parent_id)
            .where(Node.id == current_parent)
            .where(Node.owner_id == current_user.id)
        )
        result = await session.execute(query)
        parent_row = result.first()
        current_parent = parent_row[0] if parent_row else None


# Tag Management
@router.post("/{node_id}/tags/{tag_id}", status_code=201)
async def attach_tag_to_node(
    node_id: UUID,
    tag_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Attach a tag to a node"""
    
    # Verify node exists and belongs to user
    node_query = select(Node).where(Node.id == node_id, Node.owner_id == current_user.id)
    node_result = await session.execute(node_query)
    node = node_result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Verify tag exists and belongs to user
    tag_query = select(Tag).where(Tag.id == tag_id, Tag.owner_id == current_user.id)
    tag_result = await session.execute(tag_query)
    tag = tag_result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Check if already attached using a direct query to avoid lazy loading
    from app.models.node_associations import node_tags
    existing_query = select(node_tags).where(
        node_tags.c.node_id == node_id,
        node_tags.c.tag_id == tag_id
    )
    existing_result = await session.execute(existing_query)
    existing = existing_result.first()
    
    if not existing:
        # Use direct insert into association table
        from sqlalchemy import insert
        insert_stmt = insert(node_tags).values(
            node_id=node_id,
            tag_id=tag_id
        )
        await session.execute(insert_stmt)
        await session.commit()
    
    return {"message": "Tag attached to node"}


@router.delete("/{node_id}/tags/{tag_id}", status_code=204)
async def detach_tag_from_node(
    node_id: UUID,
    tag_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detach a tag from a node"""
    
    # Verify node exists and belongs to user
    node_query = select(Node).where(Node.id == node_id, Node.owner_id == current_user.id)
    node_result = await session.execute(node_query)
    node = node_result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Verify tag exists and belongs to user
    tag_query = select(Tag).where(Tag.id == tag_id, Tag.owner_id == current_user.id)
    tag_result = await session.execute(tag_query)
    tag = tag_result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Check if tag is attached using direct query to avoid lazy loading
    from app.models.node_associations import node_tags
    existing_query = select(node_tags).where(
        node_tags.c.node_id == node_id,
        node_tags.c.tag_id == tag_id
    )
    existing_result = await session.execute(existing_query)
    existing = existing_result.first()
    
    if existing:
        # Use direct delete from association table
        from sqlalchemy import delete
        delete_stmt = delete(node_tags).where(
            node_tags.c.node_id == node_id,
            node_tags.c.tag_id == tag_id
        )
        await session.execute(delete_stmt)
        await session.commit()


@router.get("/{node_id}/tags")
async def get_node_tags(
    node_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tags attached to a node"""
    
    # Verify node exists and belongs to user
    node_query = (
        select(Node)
        .options(selectinload(Node.tags))
        .where(Node.id == node_id, Node.owner_id == current_user.id)
    )
    node_result = await session.execute(node_query)
    node = node_result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return [
        {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "color": tag.color
        }
        for tag in node.tags
    ]


# Smart Folder Specific Endpoints

@router.post("/smart_folder/preview", response_model=List[NodeResponseUnion])
async def preview_smart_folder_rules_new(
    rules: dict,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=10, le=50)
):
    """Preview the results of smart folder rules without creating the folder"""
    
    # Validate rules
    rules_engine = SmartFolderRulesEngine(session)
    validation_errors = rules_engine.validate_rules(rules)
    if validation_errors:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid rules: {'; '.join(validation_errors)}"
        )
    
    # Preview results
    preview_nodes = await rules_engine.preview_smart_folder_results(
        rules, current_user.id, limit
    )
    
    # Convert to response format
    responses = []
    for node in preview_nodes:
        response = await convert_node_to_response(node, session)
        responses.append(response)
    
    return responses


@router.get("/{smart_folder_id}/contents", response_model=List[NodeResponseUnion])
async def get_smart_folder_contents(
    smart_folder_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0)
):
    """Get the contents of a smart folder by evaluating its rules"""
    
    # Get the smart folder
    query = select(SmartFolder).where(
        SmartFolder.id == smart_folder_id,
        SmartFolder.owner_id == current_user.id
    )
    result = await session.execute(query)
    smart_folder = result.scalar_one_or_none()
    
    if not smart_folder:
        raise HTTPException(status_code=404, detail="Smart folder not found")
    
    # Evaluate rules and get matching nodes
    rules_engine = SmartFolderRulesEngine(session)
    matching_nodes = await rules_engine.evaluate_smart_folder(smart_folder, current_user.id)
    
    # Apply pagination
    paginated_nodes = matching_nodes[offset:offset + limit]
    
    # Convert to response format
    responses = []
    for node in paginated_nodes:
        response = await convert_node_to_response(node, session)
        responses.append(response)
    
    return responses


@router.post("/{smart_folder_id}/preview", response_model=List[NodeResponseUnion])
async def preview_smart_folder_rules(
    smart_folder_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=10, le=50)
):
    """Preview the results of a smart folder's current rules"""
    
    # Get the smart folder
    query = select(SmartFolder).where(
        SmartFolder.id == smart_folder_id,
        SmartFolder.owner_id == current_user.id
    )
    result = await session.execute(query)
    smart_folder = result.scalar_one_or_none()
    
    if not smart_folder:
        raise HTTPException(status_code=404, detail="Smart folder not found")
    
    # Preview results
    rules_engine = SmartFolderRulesEngine(session)
    preview_nodes = await rules_engine.preview_smart_folder_results(
        smart_folder.rules, current_user.id, limit
    )
    
    # Convert to response format
    responses = []
    for node in preview_nodes:
        response = await convert_node_to_response(node, session)
        responses.append(response)
    
    return responses


@router.put("/{smart_folder_id}/rules", response_model=SmartFolderResponse)
async def update_smart_folder_rules(
    smart_folder_id: UUID,
    rules: dict,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a smart folder's rules"""
    
    # Get the smart folder
    query = select(SmartFolder).where(
        SmartFolder.id == smart_folder_id,
        SmartFolder.owner_id == current_user.id
    )
    result = await session.execute(query)
    smart_folder = result.scalar_one_or_none()
    
    if not smart_folder:
        raise HTTPException(status_code=404, detail="Smart folder not found")
    
    # Validate rules
    rules_engine = SmartFolderRulesEngine(session)
    validation_errors = rules_engine.validate_rules(rules)
    if validation_errors:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid rules: {'; '.join(validation_errors)}"
        )
    
    # Update rules
    smart_folder.rules = rules
    await session.commit()
    await session.refresh(smart_folder)
    
    return await convert_node_to_response(smart_folder, session)


@router.post("/{node_id}/create-template", response_model=TemplateResponse)
async def create_template_from_node(
    node_id: UUID,
    category: Optional[str] = None,
    description: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new template based on an existing node hierarchy (original node remains unchanged)"""
    
    # Get the source node
    source_node = await get_node_by_id_raw(node_id, session, current_user)
    
    if source_node.node_type == "template":
        raise HTTPException(status_code=400, detail="Cannot create template from another template")
    
    # Create new template node
    template = Template(
        owner_id=current_user.id,
        parent_id=None,  # Templates are root nodes
        title=f"{source_node.title} Template",  # Add "Template" suffix to differentiate
        sort_order=0,
        description=description,
        category=category,
        usage_count=0
    )
    
    session.add(template)
    await session.flush()  # Get ID without committing
    
    # Recursively copy the hierarchy (source node stays unchanged)
    await _copy_node_hierarchy(source_node, template.id, session)
    
    await session.commit()
    await session.refresh(template)
    
    return await convert_node_to_response(template, session)


async def _copy_node_hierarchy(source_node: Node, new_parent_id: Optional[UUID], session: AsyncSession, name_override: Optional[str] = None) -> Node:
    """Recursively copy a node hierarchy"""
    
    # Create the new node based on the source type
    if source_node.node_type == "task":
        source_task = await session.execute(select(Task).where(Task.id == source_node.id))
        task = source_task.scalar_one()
        
        new_node = Task(
            owner_id=source_node.owner_id,
            parent_id=new_parent_id,
            title=name_override or source_node.title,
            sort_order=source_node.sort_order,
            description=task.description,
            status=task.status,
            priority=task.priority,
            due_at=None,  # Don't copy dates
            earliest_start_at=None,
            completed_at=None,
            archived=False,  # Don't copy archived status
            recurrence_rule=task.recurrence_rule,
            recurrence_anchor=None
        )
    
    elif source_node.node_type == "note":
        source_note = await session.execute(select(Note).where(Note.id == source_node.id))
        note = source_note.scalar_one()
        
        new_node = Note(
            owner_id=source_node.owner_id,
            parent_id=new_parent_id,
            title=name_override or source_node.title,
            sort_order=source_node.sort_order,
            body=note.body
        )
    
    elif source_node.node_type == "smart_folder":
        source_sf = await session.execute(select(SmartFolder).where(SmartFolder.id == source_node.id))
        sf = source_sf.scalar_one()
        
        new_node = SmartFolder(
            owner_id=source_node.owner_id,
            parent_id=new_parent_id,
            title=name_override or source_node.title,
            sort_order=source_node.sort_order,
            rules=sf.rules,
            auto_refresh=sf.auto_refresh,
            description=sf.description
        )
    
    else:  # Regular folder/node
        new_node = Node(
            owner_id=source_node.owner_id,
            parent_id=new_parent_id,
            title=name_override or source_node.title,
            sort_order=source_node.sort_order,
            node_type="node"
        )
    
    session.add(new_node)
    await session.flush()  # Get the ID without committing
    
    # Copy children recursively
    children_query = select(Node).where(Node.parent_id == source_node.id)
    children_result = await session.execute(children_query)
    children = children_result.scalars().all()
    
    for child in children:
        await _copy_node_hierarchy(child, new_node.id, session)
    
    return new_node


# Template target node endpoints
@router.get("/templates/{template_id}/target-node")
async def get_template_target_node(
    template_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the target node ID for a template"""
    
    # Get the template
    template_query = select(Template).where(
        Template.id == template_id,
        Template.owner_id == current_user.id
    )
    result = await session.execute(template_query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"target_node_id": str(template.target_node_id) if template.target_node_id else None}


@router.put("/templates/{template_id}/target-node")
async def set_template_target_node(
    template_id: UUID,
    request: dict,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set the target node ID for a template"""
    
    # Get the template
    template_query = select(Template).where(
        Template.id == template_id,
        Template.owner_id == current_user.id
    )
    result = await session.execute(template_query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get target_node_id from request
    target_node_id_str = request.get("target_node_id")
    
    # Validate target node exists and belongs to user if provided
    if target_node_id_str:
        try:
            target_node_uuid = UUID(target_node_id_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid target node ID format")
        
        # Check if target node exists and belongs to user
        target_query = select(Node).where(
            Node.id == target_node_uuid,
            Node.owner_id == current_user.id
        )
        target_result = await session.execute(target_query)
        target_node = target_result.scalar_one_or_none()
        
        if not target_node:
            raise HTTPException(status_code=404, detail="Target node not found")
        
        template.target_node_id = target_node_uuid
    else:
        # Clear target node (set to None)
        template.target_node_id = None
    
    await session.commit()
    
    return {"success": True, "target_node_id": target_node_id_str}


@router.get("/templates/{template_id}/create-container")
async def get_template_create_container(
    template_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the create_container setting for a template"""
    
    # Get the template
    template_query = select(Template).where(
        Template.id == template_id,
        Template.owner_id == current_user.id
    )
    result = await session.execute(template_query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"create_container": template.create_container}


@router.put("/templates/{template_id}/create-container")
async def set_template_create_container(
    template_id: UUID,
    request: dict,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set the create_container setting for a template"""
    
    # Get the template
    template_query = select(Template).where(
        Template.id == template_id,
        Template.owner_id == current_user.id
    )
    result = await session.execute(template_query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get create_container from request
    create_container = request.get("create_container")
    
    if create_container is None:
        raise HTTPException(status_code=400, detail="create_container field is required")
    
    if not isinstance(create_container, bool):
        raise HTTPException(status_code=400, detail="create_container must be a boolean")
    
    template.create_container = create_container
    await session.commit()
    
    return {"success": True, "create_container": create_container}