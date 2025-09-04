# FastGTD MCP Tools Index

## Current Available Tools (25 tools)

### ✅ Navigation & Search
- **`get_node_tree`** - Browse hierarchical structure of tasks, notes, and folders
  - Parameters: `root_id` (optional), `max_depth` (default: 10)
  - Returns: Tree structure with all child nodes
  - Status: ✅ Working

- **`search_nodes`** - Search tasks, notes, and folders by content
  - Parameters: `query` (required), `node_type` (optional), `limit` (default: 50)
  - Returns: List of matching nodes with titles and content
  - Status: ✅ Working

### 📝 Task Management
- **`add_task_to_inbox`** - Add new task to user's default inbox
  - Parameters: `title` (required), `description`, `priority` (high/medium/low)
  - Returns: Created task details
  - Status: ✅ Working

- **`add_task_to_current_node`** - Add task to current location
  - Parameters: `title` (required), `description`, `priority`
  - Returns: Created task details
  - Status: ✅ Working

- **`add_task_to_node_id`** - Add task to specific folder by ID
  - Parameters: `node_id` (required), `task_title`, `description`, `priority`
  - Returns: Created task details
  - Status: ✅ Working

- **`create_task`** - Simplified task creation with auto-location detection
  - Parameters: `title` (required), `description`, `priority`, `parent_id` (optional)
  - Returns: Created task details with ID
  - Status: ✅ Working

- **`update_task`** - Update existing task properties
  - Parameters: `task_id` (required), `title`, `description`, `priority` (low/medium/high/urgent), `status` (todo/in_progress/done/dropped)
  - Returns: Updated task details
  - Status: ✅ Working

- **`complete_task`** - Mark task as completed
  - Parameters: `task_id` (required)
  - Returns: Updated task with done status
  - Status: ✅ Working

- **`delete_task`** - Permanently delete task
  - Parameters: `task_id` (required)  
  - Returns: Success confirmation
  - Status: ✅ Working

### 📁 Organization  
- **`add_folder_to_current_node`** - Create new folder in current location
  - Parameters: `title` (required)
  - Returns: Created folder details
  - Status: ✅ Working

- **`create_folder`** - Create new folder with auto-location detection
  - Parameters: `title` (required), `parent_id` (optional)
  - Returns: Created folder details with ID
  - Status: ✅ Working

- **`move_node`** - Move tasks, notes, or folders to different locations
  - Parameters: `node_id` (required), `new_parent_id` (optional), `new_sort_order` (optional)
  - Returns: Success confirmation with move details
  - Status: ✅ Working

- **`add_note_to_current_node`** - Create note in current location
  - Parameters: `title` (required), `content`
  - Returns: Created note details
  - Status: ✅ Working

- **`add_note_to_node_id`** - Create note in specific node by ID
  - Parameters: `node_id` (required), `title` (required), `content` (optional)
  - Returns: Created note details with note ID
  - Status: ✅ Working

- **`update_note`** - Update existing note's title and/or content
  - Parameters: `note_id` (required), `title` (optional), `content` (optional)
  - Returns: Updated note details with new title and content
  - Status: ✅ Working

### 🔍 Folder Operations
- **`get_all_folders`** - List all available folders
  - Parameters: None
  - Returns: List of all folders with IDs and titles
  - Status: ✅ Working

- **`get_folder_id`** - Find folder ID by name
  - Parameters: `folder_name` (required)
  - Returns: Folder ID if found
  - Status: ✅ Working

### 🏷️ Tagging
- **`add_tag`** - Add tags to tasks, notes, or folders (creates tag if needed)
  - Parameters: `node_id` (required), `tag_name` (required), `tag_description` (optional), `tag_color` (optional)
  - Returns: Success confirmation with tag details
  - Status: ✅ Working

- **`remove_tag`** - Remove tags from tasks, notes, or folders
  - Parameters: `node_id` (required), `tag_name` (required) 
  - Returns: Success confirmation with tag removal details
  - Status: ✅ Working

### 🕐 Quick Actions
- **`get_today_tasks`** - Get all tasks that are due today
  - Parameters: None
  - Returns: List of tasks with due dates matching today's date
  - Status: ✅ Working

- **`get_overdue_tasks`** - Get all tasks that are overdue (due date in the past)
  - Parameters: None
  - Returns: List of overdue tasks sorted by most overdue first, includes days overdue count
  - Status: ✅ Working

### 🤖 Smart Folder Operations
- **`get_smart_folder_contents`** - Get contents of smart folder by evaluating its rules
  - Parameters: `smart_folder_id` (required), `limit` (default: 100, max: 500), `offset` (default: 0)
  - Returns: List of nodes matching smart folder rules with pagination info
  - Status: ✅ Working

### 📋 Template Operations
- **`list_templates`** - List all available templates with optional category filter
  - Parameters: `category` (optional), `limit` (default: 50, max: 100), `offset` (default: 0)
  - Returns: List of templates with details, usage counts, and pagination info
  - Status: ✅ Working

- **`search_templates`** - Search for templates by name or description
  - Parameters: `query` (required), `category` (optional), `limit` (default: 50, max: 100)  
  - Returns: List of matching templates with details and IDs for instantiation
  - Status: ✅ Working

- **`instantiate_template`** - Create new instance from template with all its contents
  - Parameters: `template_id` (required), `name` (required), `parent_id` (optional)
  - Returns: Created instance details (folder containing template contents)
  - Status: ✅ Working

## Tool Testing

Use `testai.py` to test any tool:

```bash
./venv/bin/python testai.py "search for cabinet tasks"
./venv/bin/python testai.py "create a task called 'test task'"
./venv/bin/python testai.py "show me the folder structure"
```

## Authentication

All tools automatically receive the authenticated user's context via:
- `auth_token` - JWT bearer token
- `current_node_id` - Current folder context

## API Integration

Tools connect to FastGTD backend via:
- Base URL: `http://localhost:8003`
- Endpoints: `/nodes/`, `/settings/default-node`
- Headers: `Authorization: Bearer {token}`

## Implementation Status

- **Phase 1**: ✅ Complete (Navigation & Search)
- **Phase 2**: ✅ Complete (Task management essentials)  
- **Phase 3**: ✅ Complete (Organization tools)
- **Phase 4**: ✅ Complete (Quick actions)

## Phase 4 Complete! (Quick Actions)

✅ All Tools Implemented & Tested:
1. **`get_today_tasks`** - Get all tasks due today with date filtering
2. **`get_overdue_tasks`** - Get overdue tasks sorted by days overdue (excludes completed tasks)

🎉 **Phase 4 Status**: All quick action tools are working perfectly!

## All Phases Complete! 🎊

🚀 **FastGTD MCP Tools Implementation Status**: **COMPLETE**

All 4 phases have been successfully implemented:
- ✅ **Phase 1**: Navigation & Search (2 tools)
- ✅ **Phase 2**: Task Management Essentials (6 tools)  
- ✅ **Phase 3**: Organization (4 tools)
- ✅ **Phase 4**: Quick Actions (2 tools)
- ✅ **Bonus**: Enhanced `update_task` with all Task model fields
- ✅ **Additional**: `update_note` for note content management
- ✅ **Additional**: `get_smart_folder_contents` for smart folder automation
- ✅ **Additional**: `instantiate_template` for template-based project creation

**Total: 25 fully functional MCP tools ready for AI assistant integration!**