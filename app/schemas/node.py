from datetime import datetime
from typing import Optional, List, Union, Literal, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.enums import TaskStatus, TaskPriority
from app.schemas.tag import TagResponse


# Base Node schemas
class NodeBase(BaseModel):
    """Base schema for all node types"""
    title: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[UUID] = None
    sort_order: int = Field(default=0)

    model_config = ConfigDict(from_attributes=True)


class NodeCreate(NodeBase):
    """Schema for creating nodes - requires node_type"""
    node_type: Literal["task", "note", "smart_folder", "template"]


class NodeUpdate(BaseModel):
    """Schema for updating nodes - all fields optional"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[UUID] = None
    sort_order: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Task-specific schemas
class TaskData(BaseModel):
    """Task-specific data"""
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_at: Optional[datetime] = None
    earliest_start_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    archived: bool = False
    recurrence_rule: Optional[str] = None
    recurrence_anchor: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(NodeCreate):
    """Schema for creating tasks"""
    node_type: Literal["task"] = "task"
    task_data: TaskData = Field(default_factory=TaskData)


class TaskUpdate(NodeUpdate):
    """Schema for updating tasks"""
    task_data: Optional[TaskData] = None


# Note-specific schemas
class NoteData(BaseModel):
    """Note-specific data"""
    body: str = Field(..., min_length=1)

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(NodeCreate):
    """Schema for creating notes"""
    node_type: Literal["note"] = "note"
    note_data: NoteData


class NoteUpdate(NodeUpdate):
    """Schema for updating notes"""
    note_data: Optional[NoteData] = None


# Folder-specific schemas
class FolderData(BaseModel):
    """Folder-specific data"""
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FolderCreate(NodeCreate):
    """Schema for creating folders - organizational containers with optional description"""
    node_type: Literal["folder"] = "folder"
    folder_data: Optional[FolderData] = None


class FolderUpdate(NodeUpdate):
    """Schema for updating folders"""
    folder_data: Optional[FolderData] = None


# Smart Folder-specific schemas
class SmartFolderCondition(BaseModel):
    """Individual filter condition for smart folders"""
    type: Literal["tag_contains", "node_type", "parent_node", "parent_ancestor", "task_status", "task_priority", "title_contains", "has_children"]
    operator: Literal["equals", "in", "any", "all", "contains", "not_equals"]
    values: List[str]

    model_config = ConfigDict(from_attributes=True)


class SmartFolderRules(BaseModel):
    """Rules schema for smart folder filtering"""
    conditions: List[SmartFolderCondition] = Field(default_factory=list)
    logic: Literal["AND", "OR"] = "AND"

    model_config = ConfigDict(from_attributes=True)


class SmartFolderData(BaseModel):
    """Smart folder-specific data"""
    rule_id: Optional[UUID] = None  # Reference to the rule this smart folder uses
    rules: Optional[dict] = None  # DEPRECATED - Raw dict for JSON storage, kept for backward compatibility
    auto_refresh: Optional[bool] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SmartFolderCreate(NodeCreate):
    """Schema for creating smart folders"""
    node_type: Literal["smart_folder"] = "smart_folder"
    smart_folder_data: SmartFolderData = Field(default_factory=SmartFolderData)


class SmartFolderUpdate(NodeUpdate):
    """Schema for updating smart folders"""
    smart_folder_data: Optional[SmartFolderData] = None


# Template-specific schemas
class TemplateData(BaseModel):
    """Template-specific data"""
    description: Optional[str] = None
    category: Optional[str] = None
    usage_count: int = Field(default=0)
    target_node_id: Optional[UUID] = None
    create_container: bool = Field(default=True)

    model_config = ConfigDict(from_attributes=True)


class TemplateCreate(NodeCreate):
    """Schema for creating templates"""
    node_type: Literal["template"] = "template"
    template_data: TemplateData = Field(default_factory=TemplateData)


class TemplateUpdate(NodeUpdate):
    """Schema for updating templates"""
    template_data: Optional[TemplateData] = None


# Response schemas
class NodeResponse(NodeBase):
    """Base response schema for nodes"""
    id: UUID
    owner_id: UUID
    node_type: str
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_list: bool = False
    children_count: int = 0
    
    # Related data
    tags: List[TagResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(NodeResponse):
    """Response schema for tasks"""
    node_type: Literal["task"] = "task"
    task_data: TaskData

    model_config = ConfigDict(from_attributes=True)


class NoteResponse(NodeResponse):
    """Response schema for notes"""
    node_type: Literal["note"] = "note"
    note_data: NoteData

    model_config = ConfigDict(from_attributes=True)


class FolderResponse(NodeResponse):
    """Response schema for folders - organizational containers with optional description"""
    node_type: Literal["folder"] = "folder"
    folder_data: Optional[FolderData] = None

    model_config = ConfigDict(from_attributes=True)


class SmartFolderResponse(NodeResponse):
    """Response schema for smart folders"""
    node_type: Literal["smart_folder"] = "smart_folder"
    smart_folder_data: SmartFolderData

    model_config = ConfigDict(from_attributes=True)


class TemplateResponse(NodeResponse):
    """Response schema for templates"""
    node_type: Literal["template"] = "template"
    template_data: TemplateData

    model_config = ConfigDict(from_attributes=True)


# Union type for polymorphic responses
NodeResponseUnion = Union[TaskResponse, NoteResponse, FolderResponse, SmartFolderResponse, TemplateResponse]


# Tree/hierarchy schemas
class NodeTreeItem(BaseModel):
    """Schema for tree/hierarchy representations"""
    id: UUID
    title: str
    node_type: str
    parent_id: Optional[UUID]
    sort_order: int
    is_list: bool
    children_count: int
    level: int = 0
    expanded: bool = False
    
    # Type-specific preview data
    preview_data: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class NodeTree(BaseModel):
    """Schema for tree responses with metadata"""
    root_id: Optional[UUID]
    items: List[NodeTreeItem]
    total_count: int

    model_config = ConfigDict(from_attributes=True)


# Bulk operations
class NodeBulkCreate(BaseModel):
    """Schema for bulk node creation"""
    nodes: List[Union[TaskCreate, NoteCreate, FolderCreate, SmartFolderCreate, TemplateCreate]]

    model_config = ConfigDict(from_attributes=True)


class NodeBulkUpdate(BaseModel):
    """Schema for bulk node updates"""
    updates: List[tuple[UUID, Union[TaskUpdate, NoteUpdate, FolderUpdate, SmartFolderUpdate, TemplateUpdate]]]

    model_config = ConfigDict(from_attributes=True)


class NodeMove(BaseModel):
    """Schema for moving nodes in hierarchy"""
    node_id: UUID
    new_parent_id: Optional[UUID]
    new_sort_order: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class NodeReorder(BaseModel):
    """Schema for reordering nodes"""
    node_ids: List[UUID] = Field(..., min_length=1)
    parent_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


# Search and filtering
class NodeFilter(BaseModel):
    """Schema for filtering nodes"""
    node_type: Optional[str] = None
    parent_id: Optional[UUID] = None
    search: Optional[str] = None
    tags: Optional[List[UUID]] = None
    status: Optional[TaskStatus] = None  # Only applies to tasks
    priority: Optional[TaskPriority] = None  # Only applies to tasks
    archived: Optional[bool] = None  # Only applies to tasks
    has_children: Optional[bool] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

    model_config = ConfigDict(from_attributes=True)


# Factory functions for creating polymorphic responses
def create_node_response(node_data: dict, task_data: dict = None, note_data: dict = None, smart_folder_data: dict = None, template_data: dict = None, folder_data: dict = None) -> NodeResponseUnion:
    """Factory function to create appropriate node response based on type"""
    node_type = node_data.get("node_type")

    if node_type == "task":
        return TaskResponse(
            **node_data,
            task_data=TaskData(**(task_data or {}))
        )
    elif node_type == "note":
        return NoteResponse(
            **node_data,
            note_data=NoteData(**(note_data or {}))
        )
    elif node_type == "folder":
        return FolderResponse(
            **node_data,
            folder_data=FolderData(**(folder_data or {})) if folder_data else None
        )
    elif node_type == "smart_folder":
        return SmartFolderResponse(
            **node_data,
            smart_folder_data=SmartFolderData(**(smart_folder_data or {}))
        )
    elif node_type == "template":
        return TemplateResponse(
            **node_data,
            template_data=TemplateData(**(template_data or {}))
        )
    else:
        raise ValueError(f"Unknown node type: {node_type}")


# Validation helpers
def validate_node_type(v):
    """Validate node_type values"""
    if v not in ["task", "note", "folder", "smart_folder", "template"]:
        raise ValueError("node_type must be 'task', 'note', 'folder', 'smart_folder', or 'template'")
    return v