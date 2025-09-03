# FastGTD MCP Tools - Essential Development Plan

## Prerequisites & Project Layout

### Key Files & Locations
- **MCP Server**: `app/ai/fastgtd_mcp_server.py` - Main MCP tool implementations
- **Test Script**: `./venv/bin/python testai.py` - Test MCP tools with AI
- **API Server**: Running on `http://localhost:8003` via `./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8003`
- **Auth Token**: Available in environment as `ACCESS_TOKEN`

### FastGTD API Structure
- **Nodes Endpoint**: `POST/PUT/DELETE http://localhost:8003/nodes/` - Unified system for tasks, notes, folders
- **Node Types**: `task`, `note`, `folder` (notes with "Container folder" body), `smart_folder`, `template`
- **Task Payload**: `{"node_type": "task", "title": "...", "task_data": {"description": "...", "priority": "...", "status": "todo"}}`
- **Authentication**: `Authorization: Bearer {token}` header required

### Testing Workflow
- **Fresh Test**: `./venv/bin/python testai.py --clear "test prompt"` 
- **With History**: `./venv/bin/python testai.py "test prompt"`
- **History File**: `testai_history.json` accumulates conversation context

### MCP Tool Structure
1. Add function to `fastgtd_mcp_server.py`
2. Add to `TOOL_HANDLERS` mapping
3. Add `Tool()` definition in `handle_list_tools()`
4. Test with `testai.py`

## Must-Have MCP Tools (Priority Order)

### Phase 1: Core Navigation & Search
- [x] `get_node_tree` - Browse task/note hierarchy
- [x] `search_nodes` - Find tasks/notes by content

### Phase 2: Task Management Essentials  
- [x] `create_task` - Create new tasks with title, description, priority
- [x] `update_task` - Modify task content, status, priority
- [x] `complete_task` - Mark tasks as done
- [x] `delete_task` - Remove tasks

### Phase 3: Basic Organization
- [x] `create_folder` - Organize tasks into folders  
- [x] `move_node` - Move tasks/notes between folders
- [x] `add_tag` - Tag tasks for categorization
- [x] `remove_tag` - Remove tags from tasks

### Phase 4: Quick Actions
- [x] `get_today_tasks` - Show today's due tasks
- [x] `get_overdue_tasks` - Show overdue tasks
- [x] ~~`set_due_date` - Set/update task due dates~~ (REDUNDANT: use `update_task`)
- [x] ~~`set_priority` - Set task priority (high/medium/low)~~ (REDUNDANT: use `update_task`)

## Development Flow (Strict Process)

### Per-Tool Workflow:
1. **Add Tool** - Implement function in `fastgtd_mcp_server.py`
2. **Test Tool** - Validate with `./venv/bin/python testai.py "test prompt"`
   - Use `--clear` flag to start fresh: `./venv/bin/python testai.py --clear "test prompt"`
   - Without `--clear`, conversation history accumulates in `testai_history.json`
3. **Document Tool** - Update `mcp_index.md` with tool details
4. **Move On** - Only proceed to next tool after current one works

### Development Guidelines:
1. **Test-First**: Use `testai.py` to validate each tool immediately
2. **One at a Time**: Implement and test each tool completely before moving to next
3. **Error Handling**: Each tool must handle API errors gracefully  
4. **Documentation**: Update index immediately after successful test

## Success Criteria

Each tool must:
- Work on first test with `testai.py`
- Handle common error cases (not found, permission denied)
- Return clear, actionable responses
- Follow FastGTD API patterns consistently

## Additional Implemented Tools (Post-Phase 4)

- [x] `update_note` - Update existing note title and/or content
- [x] `get_smart_folder_contents` - Get contents of smart folder by evaluating its rules
- [x] `instantiate_template` - Create new instance from template with all its contents
- [x] `list_templates` - List all available templates with optional category filter
- [x] `search_templates` - Search for templates by name or description

## Not Essential (Future)

- Bulk operations
- Advanced search filters  
- Smart folder management
- Analytics/reporting tools
- Complex workflow automation