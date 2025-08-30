#!/usr/bin/env python3
"""
FastGTD MCP Server - Test Implementation
Simple MCP server with one test tool to verify authentication headers.
"""

import asyncio
import json
import logging
from datetime import datetime
import os
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

# Set up file logging
log_dir = "/tmp/fastgtd_mcp_logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"mcp_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info(f"=== FastGTD MCP Server Starting - Log file: {log_file} ===")

# Initialize MCP server
server = Server("fastgtd-test")

async def add_task_to_inbox(title: str, description: str = "", priority: str = "medium", auth_token: str = "", current_node_id: str = "") -> dict:
    """Add a task to the user's default node (inbox)"""
    logger.info(f"🧪 add_task_to_inbox CALLED - title='{title}', description='{description}', priority='{priority}', auth_token_present={bool(auth_token)}")
    
    try:
        import httpx
        
        print(f"🧪 MCP DEBUG - add_task_to_inbox called:")
        print(f"   Title: {title}")
        print(f"   Description: {description}")
        print(f"   Priority: {priority}")
        print(f"   Auth token present: {bool(auth_token)}")
        
        # FastGTD API endpoint
        url = "http://localhost:8003/nodes/"
    
    except Exception as e:
        print(f"❌ MCP ERROR in setup: {str(e)}")
        return {
            "success": False,
            "error": f"MCP tool setup failed: {str(e)}"
        }
    
    # Create task payload for unified node system
    task_payload = {
        "node_type": "task",
        "title": title,
        "task_data": {
            "description": description,
            "priority": priority,
            "status": "todo",
            "archived": False
        }
    }
    
    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        async with httpx.AsyncClient() as client:
            # First, get the user's default node (inbox)
            if auth_token:
                default_node_response = await client.get(
                    "http://localhost:8003/settings/default-node",
                    headers=headers
                )
                
                if default_node_response.status_code == 200:
                    default_data = default_node_response.json()
                    default_node_id = default_data.get("node_id")
                    print(f"📋 Default node response: {default_data}")
                    if default_node_id:
                        task_payload["parent_id"] = default_node_id
                        print(f"🎯 Setting parent_id to default node: {default_node_id}")
                    else:
                        print(f"⚠️  No default node set for user - task will be added to root")
                else:
                    print(f"⚠️  Failed to get default node: HTTP {default_node_response.status_code}")
                    
            print(f"📤 Final task payload: {task_payload}")
            
            response = await client.post(
                url,
                json=task_payload,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                task_data = response.json()
                return {
                    "success": True,
                    "message": f"Task '{title}' added to inbox successfully",
                    "task_id": task_data.get("id"),
                    "task": task_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to add task: HTTP {response.status_code}",
                    "details": response.text
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to add task to inbox: {str(e)}"
        }

async def add_folder_to_current_node(title: str, auth_token: str = "", current_node_id: str = "") -> dict:
    """Add a folder to the current node"""
    try:
        import httpx
        
        print(f"📁 MCP DEBUG - add_folder_to_current_node called:")
        print(f"   Title: {title}")
        print(f"   Current node ID: {current_node_id}")
        print(f"   Auth token present: {bool(auth_token)}")
        
        if not current_node_id:
            return {"success": False, "error": "No current node ID provided"}
        
        # FastGTD API endpoint
        url = "http://localhost:8003/nodes/"
        
        # Create folder payload - folders are notes with "Container folder" body
        folder_payload = {
            "node_type": "note",
            "title": title,
            "parent_id": current_node_id,
            "note_data": {
                "body": "Container folder"
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=folder_payload, headers=headers)
            
        if response.status_code == 200:
            folder_data = response.json()
            return {
                "success": True,
                "message": f"Folder '{title}' added to current node successfully",
                "folder_id": folder_data.get("id"),
                "folder": folder_data
            }
        else:
            error_text = response.text
            print(f"❌ API Error {response.status_code}: {error_text}")
            return {
                "success": False,
                "error": f"API request failed with status {response.status_code}: {error_text}"
            }
            
    except Exception as e:
        print(f"❌ MCP ERROR in add_folder_to_current_node: {str(e)}")
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}"
        }

async def add_task_to_current_node(title: str, description: str = "", priority: str = "medium", auth_token: str = "", current_node_id: str = "") -> dict:
    """Add a task to the user's currently selected node"""
    try:
        import httpx
        
        print(f"🧪 MCP DEBUG - add_task_to_current_node called:")
        print(f"   Title: {title}")
        print(f"   Description: {description}")
        print(f"   Priority: {priority}")
        print(f"   Auth token present: {bool(auth_token)}")
        print(f"   Current node ID: {current_node_id}")
        
        if not current_node_id:
            return {
                "success": False,
                "error": "No current node ID provided - cannot determine where to add task"
            }
        
        # FastGTD API endpoint
        url = "http://localhost:8003/nodes/"
    
    except Exception as e:
        print(f"❌ MCP ERROR in setup: {str(e)}")
        return {
            "success": False,
            "error": f"MCP tool setup failed: {str(e)}"
        }
    
    # Create task payload for unified node system
    task_payload = {
        "node_type": "task",
        "title": title,
        "parent_id": current_node_id,  # Use provided current node directly
        "task_data": {
            "description": description,
            "priority": priority,
            "status": "todo",
            "archived": False
        }
    }
    
    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"📤 Final task payload: {task_payload}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=task_payload,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                task_data = response.json()
                return {
                    "success": True,
                    "message": f"Task '{title}' added to current node successfully",
                    "task_id": task_data.get("id"),
                    "task": task_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to add task: HTTP {response.status_code}",
                    "details": response.text
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to add task to current node: {str(e)}"
        }

async def add_note_to_current_node(title: str, content: str = "", auth_token: str = "", current_node_id: str = "") -> dict:
    """Add a note to the user's currently selected node"""
    try:
        import httpx
        
        print(f"📝 MCP DEBUG - add_note_to_current_node called:")
        print(f"   Title: {title}")
        print(f"   Content: {content}")
        print(f"   Auth token present: {bool(auth_token)}")
        print(f"   Current node ID: {current_node_id}")
        
        if not current_node_id:
            return {
                "success": False,
                "error": "No current node ID provided - cannot determine where to add note"
            }
        
        # FastGTD API endpoint
        url = "http://localhost:8003/nodes/"
    
    except Exception as e:
        print(f"❌ MCP ERROR in setup: {str(e)}")
        return {
            "success": False,
            "error": f"MCP tool setup failed: {str(e)}"
        }
    
    # Create note payload for unified node system
    note_payload = {
        "node_type": "note",
        "title": title,
        "parent_id": current_node_id,  # Use provided current node directly
        "note_data": {
            "body": content
        }
    }
    
    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"📤 Final note payload: {note_payload}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=note_payload,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                note_data = response.json()
                return {
                    "success": True,
                    "message": f"Note '{title}' added to current node successfully",
                    "note_id": note_data.get("id"),
                    "note": note_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to add note: HTTP {response.status_code}",
                    "details": response.text
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to add note to current node: {str(e)}"
        }

async def get_all_folders(auth_token: str = "", current_node_id: str = "") -> dict:
    """Get all folder names in the user's node tree for AI to help find the right folder"""
    try:
        import httpx
        
        print(f"📁 MCP DEBUG - get_all_folders called:")
        print(f"   Auth token present: {bool(auth_token)}")
        
        if not auth_token:
            return {"success": False, "error": "No authentication token provided"}
        
        # FastGTD API endpoint - get all notes (folders are notes with "Container folder" body)
        url = "http://localhost:8003/nodes/"
    
    except Exception as e:
        print(f"❌ MCP ERROR in setup: {str(e)}")
        return {
            "success": False,
            "error": f"MCP tool setup failed: {str(e)}"
        }
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Get all notes (folders are a subset of notes)
            response = await client.get(
                url,
                headers=headers,
                params={"node_type": "note", "limit": 1000}  # Get all notes
            )
            
            if response.status_code in [200, 201]:
                nodes_data = response.json()
                folders = []
                
                # Filter for folders (notes with "Container folder" body)
                for node in nodes_data:
                    if (node.get("node_type") == "note" and 
                        node.get("note_data", {}).get("body") == "Container folder"):
                        
                        folder_title = node.get("title")
                        if folder_title:
                            folders.append(folder_title)
                
                return {
                    "success": True,
                    "message": f"Found {len(folders)} folders",
                    "folders": folders
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to retrieve folders: HTTP {response.status_code}",
                    "details": response.text
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get folders: {str(e)}"
        }

async def get_folder_id(folder_name: str, auth_token: str = "", current_node_id: str = "") -> dict:
    """Get folder ID by folder name - useful for finding the specific folder to work with"""
    logger.info(f"🔍 get_folder_id CALLED - folder_name='{folder_name}', auth_token_present={bool(auth_token)}")
    
    try:
        import httpx
        
        print(f"🔍 MCP DEBUG - get_folder_id called:")
        print(f"   Folder name: {folder_name}")
        print(f"   Auth token present: {bool(auth_token)}")
        
        if not auth_token:
            return {"success": False, "error": "No authentication token provided"}
        
        if not folder_name:
            return {"success": False, "error": "Folder name is required"}
        
        # FastGTD API endpoint - get all notes (folders are notes with "Container folder" body)
        url = "http://localhost:8003/nodes/"
    
    except Exception as e:
        print(f"❌ MCP ERROR in setup: {str(e)}")
        return {
            "success": False,
            "error": f"MCP tool setup failed: {str(e)}"
        }
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Get all notes (folders are a subset of notes)
            response = await client.get(
                url,
                headers=headers,
                params={"node_type": "note", "limit": 1000}  # Get all notes
            )
            
            if response.status_code in [200, 201]:
                nodes_data = response.json()
                
                # Find folder with matching name (case-insensitive)
                folder_name_lower = folder_name.lower().strip()
                for node in nodes_data:
                    if (node.get("node_type") == "note" and 
                        node.get("note_data", {}).get("body") == "Container folder"):
                        
                        node_title = node.get("title", "").lower().strip()
                        if node_title == folder_name_lower:
                            result = {
                                "success": True,
                                "message": f"Found folder '{folder_name}'",
                                "folder_id": node.get("id"),
                                "folder_name": node.get("title")
                            }
                            logger.info(f"🔍 get_folder_id SUCCESS - found folder_id={result['folder_id']} for '{folder_name}'")
                            return result
                
                # If exact match not found, check for partial matches
                partial_matches = []
                for node in nodes_data:
                    if (node.get("node_type") == "note" and 
                        node.get("note_data", {}).get("body") == "Container folder"):
                        
                        node_title = node.get("title", "").lower().strip()
                        if folder_name_lower in node_title or node_title in folder_name_lower:
                            partial_matches.append({
                                "id": node.get("id"),
                                "title": node.get("title")
                            })
                
                if partial_matches:
                    result = {
                        "success": False,
                        "error": f"No exact match found for '{folder_name}', but found similar folders",
                        "suggestions": partial_matches
                    }
                    logger.warning(f"🔍 get_folder_id PARTIAL MATCH - no exact match for '{folder_name}', found {len(partial_matches)} similar")
                    return result
                else:
                    result = {
                        "success": False,
                        "error": f"No folder found with name '{folder_name}'"
                    }
                    logger.error(f"🔍 get_folder_id FAILED - no folder found for '{folder_name}'")
                    return result
            else:
                return {
                    "success": False,
                    "error": f"Failed to retrieve folders: HTTP {response.status_code}",
                    "details": response.text
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to find folder: {str(e)}"
        }

async def add_task_to_node_id(node_id: str, task_title: str, description: str = "", priority: str = "medium", auth_token: str = "", current_node_id: str = "") -> dict:
    """Add a task to a specific node by node ID and return the new task's ID"""
    logger.info(f"🎯 add_task_to_node_id CALLED - node_id='{node_id}', task_title='{task_title}', description='{description}', priority='{priority}', auth_token_present={bool(auth_token)}")
    
    try:
        import httpx
        
        print(f"🎯 MCP DEBUG - add_task_to_node_id called:")
        print(f"   Node ID: {node_id}")
        print(f"   Task title: {task_title}")
        print(f"   Description: {description}")
        print(f"   Priority: {priority}")
        print(f"   Auth token present: {bool(auth_token)}")
        
        if not auth_token:
            return {"success": False, "error": "No authentication token provided"}
        
        if not node_id:
            return {"success": False, "error": "Node ID is required"}
            
        if not task_title:
            return {"success": False, "error": "Task title is required"}
        
        # FastGTD API endpoint
        url = "http://localhost:8003/nodes/"
    
    except Exception as e:
        print(f"❌ MCP ERROR in setup: {str(e)}")
        return {
            "success": False,
            "error": f"MCP tool setup failed: {str(e)}"
        }
    
    # Create task payload for unified node system
    task_payload = {
        "node_type": "task",
        "title": task_title,
        "parent_id": node_id,  # Use the provided node ID
        "task_data": {
            "description": description,
            "priority": priority,
            "status": "todo",
            "archived": False
        }
    }
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    print(f"📤 Final task payload: {task_payload}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=task_payload,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                task_data = response.json()
                task_id = task_data.get("id")
                result = {
                    "success": True,
                    "message": f"Task '{task_title}' added to node successfully",
                    "task_id": task_id,
                    "node_id": node_id,
                    "task_title": task_title
                }
                logger.info(f"🎯 add_task_to_node_id SUCCESS - created task_id={task_id} in node_id={node_id}")
                return result
            else:
                result = {
                    "success": False,
                    "error": f"Failed to add task: HTTP {response.status_code}",
                    "details": response.text
                }
                logger.error(f"🎯 add_task_to_node_id FAILED - HTTP {response.status_code} for task '{task_title}' to node {node_id}")
                return result
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to add task to node: {str(e)}"
        }

# Tool handlers mapping
TOOL_HANDLERS = {
    "add_task_to_inbox": add_task_to_inbox,
    "add_task_to_current_node": add_task_to_current_node,
    "add_folder_to_current_node": add_folder_to_current_node,
    "add_note_to_current_node": add_note_to_current_node,
    "get_all_folders": get_all_folders,
    "get_folder_id": get_folder_id,
    "add_task_to_node_id": add_task_to_node_id,
}

@server.list_tools()
async def handle_list_tools():
    """List available FastGTD tools."""
    tools = [
        Tool(
            name="add_task_to_inbox",
            description="Add a new task to user's inbox (default node) - perfect for quick task capture",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title (required)"},
                    "description": {"type": "string", "description": "Task description (optional)"},
                    "priority": {"type": "string", "description": "Priority: low, medium, high (default: medium)"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="add_task_to_current_node",
            description="Add a new task to the user's currently selected node/folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title (required)"},
                    "description": {"type": "string", "description": "Task description (optional)"},
                    "priority": {"type": "string", "description": "Priority: low, medium, high (default: medium)"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="add_folder_to_current_node",
            description="Add a new folder to the user's currently selected node/folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Folder name (required)"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="add_note_to_current_node",
            description="Add a new note to the user's currently selected node/folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Note title (required)"},
                    "content": {"type": "string", "description": "Note content/body (optional)"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="get_all_folders",
            description="Get all folder names in the user's node tree - useful for AI to help find the right folder when user mentions one",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_folder_id",
            description="Get folder ID by folder name - useful for finding the specific folder to work with",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_name": {"type": "string", "description": "Name of the folder to find (required)"}
                },
                "required": ["folder_name"]
            }
        ),
        Tool(
            name="add_task_to_node_id",
            description="Add a task to a specific node by node ID and return the new task's ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "ID of the node to add the task to (required)"},
                    "task_title": {"type": "string", "description": "Title of the task to create (required)"},
                    "description": {"type": "string", "description": "Task description (optional)"},
                    "priority": {"type": "string", "description": "Priority: low, medium, high (default: medium)"}
                },
                "required": ["node_id", "task_title"]
            }
        )
    ]
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None = None):
    """Handle tool execution."""
    
    if not arguments:
        arguments = {}
        
    handler = TOOL_HANDLERS.get(name)
    if handler:
        try:
            result = await handler(**arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            error_info = {"success": False, "error": f"Tool execution failed: {str(e)}"}
            return [TextContent(type="text", text=json.dumps(error_info, indent=2))]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the FastGTD test MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fastgtd-test",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())