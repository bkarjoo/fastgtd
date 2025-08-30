# FastGTD MCP Tool Development Protocol

## Overview

This document outlines the proven paradigm for adding new MCP (Model Context Protocol) tools to the FastGTD MCP server. This protocol was developed through studying existing tools, debugging implementations, and successfully deploying the `add_note_to_current_node` tool.

## Architecture

The FastGTD MCP server (`app/ai/fastgtd_mcp_server.py`) is a stdio-based MCP server that provides AI assistants with tools to interact with the FastGTD API. It acts as a bridge between MCP clients and the FastGTD backend.

```
MCP Client (Claude, etc.) ←→ MCP Server ←→ FastGTD API (localhost:8003)
```

## Current Available Tools

1. **`add_task_to_inbox`** - Add task to user's default node (inbox)
2. **`add_task_to_current_node`** - Add task to currently selected node
3. **`add_folder_to_current_node`** - Add folder to currently selected node  
4. **`add_note_to_current_node`** - Add note to currently selected node

## The 3-Step Tool Addition Protocol

### Step 1: Implement the Tool Function

Create an async function following this exact pattern:

```python
async def your_tool_name(param1: str, param2: str = "default", auth_token: str = "", current_node_id: str = "") -> dict:
    """Brief description of what the tool does"""
    try:
        import httpx
        
        print(f"🔧 MCP DEBUG - your_tool_name called:")
        print(f"   Param1: {param1}")
        print(f"   Param2: {param2}")
        print(f"   Auth token present: {bool(auth_token)}")
        print(f"   Current node ID: {current_node_id}")
        
        # Validation (if needed)
        if not current_node_id:
            return {"success": False, "error": "No current node ID provided"}
        
        # FastGTD API endpoint
        url = "http://localhost:8003/nodes/"  # or other endpoint
    
    except Exception as e:
        print(f"❌ MCP ERROR in setup: {str(e)}")
        return {
            "success": False,
            "error": f"MCP tool setup failed: {str(e)}"
        }
    
    # Create payload for API call
    payload = {
        "node_type": "note",  # or "task", depends on tool
        "title": param1,
        "parent_id": current_node_id,
        # ... other fields
    }
    
    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"📤 Final payload: {payload}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:  # Use 200 for consistency
                data = response.json()
                return {
                    "success": True,
                    "message": f"Successfully created {param1}",
                    "id": data.get("id"),
                    "data": data
                }
            else:
                return {
                    "success": False,
                    "error": f"API request failed: HTTP {response.status_code}",
                    "details": response.text
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}"
        }
```

#### Key Function Requirements:

- **Always async** - MCP server is async
- **Standard parameters**: `auth_token: str = ""` and `current_node_id: str = ""` are automatically injected by MCP system
- **Return dict format**: Always return `{"success": bool, "message": str, ...}`
- **Error handling**: Wrap in try/except blocks
- **Debug logging**: Use print statements with emoji prefixes for debugging
- **HTTP status**: Use `response.status_code == 200` (not `in [200, 201]`)

### Step 2: Register in TOOL_HANDLERS

Add your function to the `TOOL_HANDLERS` mapping:

```python
TOOL_HANDLERS = {
    "add_task_to_inbox": add_task_to_inbox,
    "add_task_to_current_node": add_task_to_current_node,
    "add_folder_to_current_node": add_folder_to_current_node,
    "add_note_to_current_node": add_note_to_current_node,
    "your_tool_name": your_tool_name,  # Add this line
}
```

### Step 3: Add Tool Definition

Add the tool definition in the `handle_list_tools()` function:

```python
@server.list_tools()
async def handle_list_tools():
    """List available FastGTD tools."""
    tools = [
        # ... existing tools ...
        Tool(
            name="your_tool_name",
            description="Clear description of what your tool does",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "Description of param1 (required)"},
                    "param2": {"type": "string", "description": "Description of param2 (optional)"}
                },
                "required": ["param1"]  # Only list truly required params
            }
        )
    ]
    return tools
```

## Implementation Notes

### Parameter Injection
The MCP system automatically injects these parameters:
- `auth_token: str` - JWT token for API authentication
- `current_node_id: str` - ID of the currently selected node/folder

Do **not** include these in the `inputSchema` - they're handled internally.

### API Patterns
Different node types use different payload structures:

**Tasks:**
```python
{
    "node_type": "task",
    "title": title,
    "parent_id": current_node_id,
    "task_data": {
        "description": description,
        "priority": priority,
        "status": "todo",
        "archived": False
    }
}
```

**Notes:**
```python
{
    "node_type": "note", 
    "title": title,
    "parent_id": current_node_id,
    "note_data": {
        "body": content
    }
}
```

**Folders:**
```python
{
    "node_type": "note",
    "title": title, 
    "parent_id": current_node_id,
    "note_data": {
        "body": "Container folder"  # Special marker for folders
    }
}
```

### Error Handling Best Practices

1. **Always wrap in try/catch**
2. **Return consistent error format**: `{"success": False, "error": "message"}`
3. **Include debug information** in error messages
4. **Handle missing parameters** gracefully
5. **Log debug info** with print statements

## Testing Your Tool

### 1. Restart MCP Server
After making changes, restart the server:
```bash
source venv/bin/activate && python app/ai/fastgtd_mcp_server.py
```

### 2. Connect MCP Client
Configure your MCP client (Claude Desktop, etc.) with:
```json
{
  "command": "python",
  "args": ["/path/to/fastgtd/app/ai/fastgtd_mcp_server.py"],
  "cwd": "/path/to/fastgtd"
}
```

### 3. Test Tool Execution
The tool will receive parameters from the MCP client and should return success/failure status.

## Common Pitfalls

1. **Forgetting to restart server** after changes
2. **Including auth_token/current_node_id in inputSchema** (they're auto-injected)
3. **Using wrong status code check** (use `== 200`, not `in [200, 201]`)
4. **Not handling missing current_node_id** for current-node tools
5. **Inconsistent error return format**

## Deployment Checklist

- [ ] Function implemented with proper signature
- [ ] Added to TOOL_HANDLERS mapping  
- [ ] Added to handle_list_tools() with correct inputSchema
- [ ] Error handling implemented
- [ ] Debug logging added
- [ ] Server restarted
- [ ] Tool tested via MCP client

## Example: Complete Tool Implementation

See the `add_note_to_current_node` implementation in `fastgtd_mcp_server.py:243-314` for a complete working example that follows this protocol.

---

This protocol ensures consistent, reliable MCP tools that integrate seamlessly with the FastGTD API and provide a great experience for AI assistants.