"""
FastMCP-based MCP Manager for Chainlit application.
Replaces the previous Chainlit widget-based MCP management with a config-driven approach.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import McpError, ClientError


class MCPManager:
    """
    Manages MCP connections using FastMCP client with config-based server definitions.
    Replaces the previous Chainlit decorator-based approach.
    """
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "mcp_config.json"
        self.config_path = config_path
        self.client: Optional[Client] = None
        self.is_connected = False
        self.available_tools: List[Dict[str, Any]] = []
        self.config: Dict[str, Any] = {}
        
        # Tools to exclude (add tool names here to disable them)
        self.excluded_tools = {
            "directory_tree",  # Disabled: often fetches huge directories like .venv, wastes tokens
            # Only keep datetime_get_datetime, exclude other datetime formats/tools if they exist
            # Note: We'll see what other datetime tools are discovered and can add them here
            # Other examples: uncomment to disable additional filesystem tools
            # "write_file",
            # "create_directory", 
            # "move_file",
            # "search_files",
        }
        
    async def initialize(self):
        """Initialize the MCP manager with config-based servers"""
        try:
            # Load configuration
            config_file = Path(self.config_path)
            if not config_file.exists():
                print(f"⚠️  MCP config file not found: {self.config_path}")
                return False
                
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            
            # Create FastMCP client with the configuration
            self.client = Client(self.config)
            
            # Connect and initialize
            await self.client.__aenter__()
            self.is_connected = True
            
            # Discover available tools
            await self._discover_tools()
            
            print(f"✅ MCP Manager initialized with {len(self.available_tools)} tools")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize MCP Manager: {e}")
            self.is_connected = False
            return False
    
    async def _discover_tools(self):
        """Discover all available tools from connected servers"""
        if not self.client:
            return
            
        try:
            # Use FastMCP's list_tools method
            tools = await self.client.list_tools()
            
            # Convert to the format expected by the rest of the application
            self.available_tools = []
            for tool in tools:
                # Skip excluded tools
                if tool.name in self.excluded_tools:
                    print(f"🚫 Excluding tool: {tool.name}")
                    continue
                    
                tool_dict = {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
                self.available_tools.append(tool_dict)
                
            print(f"📋 Discovered tools: {[t['name'] for t in self.available_tools]}")
            
        except Exception as e:
            print(f"❌ Error discovering tools: {e}")
            self.available_tools = []
    
    def _get_server_config_for_tool(self, tool_name: str) -> Dict[str, Any]:
        """Get server config for a given tool name"""
        # For multi-server setups, tool names are prefixed with server name
        servers = self.config.get("mcpServers", {})
        
        if len(servers) == 1:
            # Single server - return its config
            return list(servers.values())[0]
        else:
            # Multi-server - find server by tool name prefix
            for server_name, server_config in servers.items():
                if tool_name.startswith(f"{server_name}_"):
                    return server_config
            # Default to empty config if no match
            return {}
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Execute a tool using FastMCP client with optional authentication"""
        if not self.client or not self.is_connected:
            raise Exception("MCP Manager not initialized or connected")
        
        # Check if tool is excluded
        if tool_name in self.excluded_tools:
            raise Exception(f"Tool '{tool_name}' has been disabled")
        
        # Check if this tool's server requires authentication or current node
        server_config = self._get_server_config_for_tool(tool_name)
        send_auth = server_config.get("sendAuth", False)
        send_current_node = server_config.get("sendCurrentNode", False)
        
        try:
            # Prepare arguments with auth and/or current node if needed
            final_arguments = arguments.copy()
            
            if send_auth and user_context:
                print(f"🔑 Sending auth context for tool: {tool_name}")
                print(f"🔑 User context: {user_context}")
                try:
                    # Generate JWT token for the user
                    from app.core.security import create_access_token
                    auth_token = create_access_token(
                        subject=user_context["user_id"], 
                        extra_claims={"email": user_context["email"]}
                    )
                    print(f"🔑 Generated auth token successfully")
                    final_arguments["auth_token"] = auth_token
                except Exception as e:
                    print(f"❌ JWT token generation failed: {str(e)}")
                    raise e
            
            if send_current_node and user_context:
                current_node_id = user_context.get("current_node_id")
                if current_node_id:
                    print(f"📍 Sending current node context for tool: {tool_name}")
                    print(f"📍 Current node ID: {current_node_id}")
                    final_arguments["current_node_id"] = current_node_id
                else:
                    print(f"⚠️  Tool {tool_name} requires current node but none provided")
            
            print(f"🔧 MCP MANAGER: Calling tool {tool_name} with args: {final_arguments}")
            result = await self.client.call_tool(tool_name, final_arguments)
            print(f"🔧 MCP MANAGER: Tool result: {result}")
            return result
            
        except ClientError as e:
            # Tool execution error on server side
            raise Exception(f"Tool execution failed: {e}")
        except McpError as e:
            # Protocol-level error
            raise Exception(f"MCP protocol error: {e}")
        except Exception as e:
            # Other errors
            raise Exception(f"Unexpected error calling tool {tool_name}: {e}")
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools in the format expected by providers"""
        return self.available_tools.copy()
    
    def get_tools_by_server(self, server_name: str) -> List[Dict[str, Any]]:
        """Get tools from a specific server (with prefix filtering)"""
        if len(self.config.get("mcpServers", {})) == 1:
            # Single server - no prefixing
            return self.available_tools.copy()
        else:
            # Multi-server - filter by prefix
            prefix = f"{server_name}_"
            return [
                tool for tool in self.available_tools 
                if tool["name"].startswith(prefix)
            ]
    
    async def cleanup(self):
        """Clean up MCP connections"""
        if self.client and self.is_connected:
            try:
                await self.client.__aexit__(None, None, None)
                self.is_connected = False
                print("✅ MCP Manager cleaned up")
            except Exception as e:
                print(f"⚠️  Error during MCP cleanup: {e}")
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a specific tool is available"""
        return any(tool["name"] == tool_name for tool in self.available_tools)
    
    def disable_tool(self, tool_name: str):
        """Dynamically disable a tool"""
        self.excluded_tools.add(tool_name)
        # Remove from available tools if present
        self.available_tools = [t for t in self.available_tools if t["name"] != tool_name]
        print(f"🚫 Disabled tool: {tool_name}")
    
    def enable_tool(self, tool_name: str):
        """Dynamically enable a previously disabled tool"""
        if tool_name in self.excluded_tools:
            self.excluded_tools.remove(tool_name)
            print(f"✅ Enabled tool: {tool_name}")
            # Would need to rediscover tools to add it back to available_tools


# Global MCP manager instance
_mcp_manager: Optional[MCPManager] = None


async def get_mcp_manager() -> MCPManager:
    """Get or create the global MCP manager instance"""
    global _mcp_manager
    
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
        await _mcp_manager.initialize()
    
    return _mcp_manager


async def initialize_mcp_manager():
    """Initialize the global MCP manager - call this at app startup"""
    global _mcp_manager
    
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
        success = await _mcp_manager.initialize()
        if success:
            print("🚀 Global MCP Manager initialized successfully")
        else:
            print("⚠️  Global MCP Manager initialization failed")
    
    return _mcp_manager


async def cleanup_mcp_manager():
    """Cleanup the global MCP manager - call this at app shutdown"""
    global _mcp_manager
    
    if _mcp_manager is not None:
        await _mcp_manager.cleanup()
        _mcp_manager = None


# Legacy compatibility functions for existing code
def get_all_tools_list() -> List[Dict[str, Any]]:
    """Legacy compatibility: get all available MCP tools"""
    if _mcp_manager and _mcp_manager.is_connected:
        return _mcp_manager.get_all_tools()
    return []


def get_mcp_tools() -> Dict[str, List[Dict[str, Any]]]:
    """Legacy compatibility: get tools organized by server"""
    if _mcp_manager and _mcp_manager.is_connected:
        # For single server, return under "default" key
        if len(_mcp_manager.config.get("mcpServers", {})) == 1:
            server_name = list(_mcp_manager.config["mcpServers"].keys())[0]
            return {server_name: _mcp_manager.get_all_tools()}
        else:
            # For multi-server, organize by server name
            result = {}
            for server_name in _mcp_manager.config.get("mcpServers", {}):
                result[server_name] = _mcp_manager.get_tools_by_server(server_name)
            return result
    return {}


async def execute_mcp_tool(tool_name: str, tool_args: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> List[Any]:
    """Execute an MCP tool using the global manager"""
    manager = await get_mcp_manager()
    return await manager.call_tool(tool_name, tool_args, user_context)