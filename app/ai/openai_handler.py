"""
OpenAI handler for FastGTD application.
Simple message-in, message-out interface without streaming or tools for now.
"""

import openai
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from .fastmcp_manager import get_mcp_manager, execute_mcp_tool

# AI Configuration
AI_CONFIG_PATH = Path(__file__).parent / "ai_config.json"

def load_ai_config() -> Dict[str, Any]:
    """Load AI configuration from config file"""
    try:
        if AI_CONFIG_PATH.exists():
            with open(AI_CONFIG_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load AI config from {AI_CONFIG_PATH}: {e}")
    
    # Return default config if file doesn't exist or can't be loaded
    return {
        "openai": {
            "default_model": "gpt-4o-mini",
            "max_tool_rounds": 5,
            "timeout": 60
        },
        "logging": {
            "enabled": True,
            "log_directory": "ailogs"
        }
    }

# Load configuration
AI_CONFIG = load_ai_config()

# AI Conversation Logging
AILOGS_DIR = Path(AI_CONFIG["logging"]["log_directory"])
AILOGS_DIR.mkdir(exist_ok=True)

def create_conversation_log_file(user_id: str = "unknown") -> Path:
    """Create a timestamped log file for AI conversation using HHMMSS format"""
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"{timestamp}.log"
    return AILOGS_DIR / filename

def log_to_file(log_file: Path, entry_type: str, content: Any, overwrite: bool = False):
    """Log an entry to the conversation file"""
    try:
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": entry_type,
            "content": content
        }
        
        mode = 'w' if overwrite else 'a'
        with open(log_file, mode, encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n")
            f.write("=" * 80 + "\n")
    except Exception as e:
        print(f"Warning: Failed to write to AI log file {log_file}: {e}")

def convert_mcp_tools_to_openai(mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert MCP tools to OpenAI function calling format"""
    if not mcp_tools:
        return []
    
    openai_tools = []
    for tool in mcp_tools:
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
        }
        openai_tools.append(openai_tool)
    
    return openai_tools

async def chat_with_openai(
    message: str,
    history: Optional[List[Dict[str, Any]]] = None,
    model: Optional[str] = None,
    user_context: Optional[Dict[str, Any]] = None,
    max_tool_rounds: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Multi-hop tool-calling chat interface:
    Repeatedly calls OpenAI; if the model requests tools, execute them,
    append results, and ask the model again—until no more tool calls.
    """
    # Use config defaults if not provided
    if model is None:
        model = AI_CONFIG["openai"]["default_model"]
    if max_tool_rounds is None:
        max_tool_rounds = AI_CONFIG["openai"]["max_tool_rounds"]
    
    # Create conversation log file
    user_id = user_context.get("user_id", "unknown") if user_context else "unknown"
    log_file = create_conversation_log_file(user_id)
    
    # Log initial conversation setup (overwrite existing file)
    log_to_file(log_file, "conversation_start", {
        "user_id": user_id,
        "model": model,
        "max_tool_rounds": max_tool_rounds,
        "user_context": user_context,
        "has_history": bool(history)
    }, overwrite=True)
    
    # Log user message
    log_to_file(log_file, "user_message", {"message": message})
    
    # Check API key before creating client
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"DEBUG: Creating OpenAI client, api_key present: {bool(api_key)}")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")

    client = openai.AsyncOpenAI(api_key=api_key)
    print(f"DEBUG: OpenAI client created successfully")

    # Build messages with history
    messages = history.copy() if history else [
        {
            "role": "system",
            "content": (
                "You are a FastGTD AI assistant. Help users with task management and productivity questions. "
                "You have access to tools that can help you provide accurate information. "
                "When users ask about the current date or time, use the get_datetime tool to provide accurate, real-time information."
            ),
        }
    ]
    messages.append({"role": "user", "content": message})

    try:
        # Prepare tools
        print(f"DEBUG: Getting MCP manager...")
        mcp_manager = await get_mcp_manager()
        print(f"DEBUG: MCP manager obtained, getting tools...")
        mcp_tools = mcp_manager.get_all_tools()
        print(f"DEBUG: Got {len(mcp_tools)} MCP tools, converting to OpenAI format...")
        openai_tools = convert_mcp_tools_to_openai(mcp_tools)
        print(f"DEBUG: Converted to {len(openai_tools)} OpenAI tools")
        actions_taken = False
        
        # Log available tools
        log_to_file(log_file, "available_tools", {
            "mcp_tools": [t["name"] for t in mcp_tools],
            "openai_tools_count": len(openai_tools)
        })
        
        # Log conversation history being sent
        log_to_file(log_file, "conversation_history", {"messages": messages})

        # Multi-round loop
        for round_num in range(max_tool_rounds):
            log_to_file(log_file, "openai_request", {
                "round": round_num + 1,
                "model": model,
                "messages_count": len(messages),
                "tools_available": len(openai_tools),
                "messages_being_sent": messages  # Log full message context
            })
            
            # Ask the model
            resp = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                stream=False,
            )
            msg = resp.choices[0].message
            
            # Log AI response
            tool_calls = getattr(msg, "tool_calls", None)
            log_to_file(log_file, "ai_response", {
                "round": round_num + 1,
                "content": msg.content,
                "has_tool_calls": bool(tool_calls),
                "tool_calls_count": len(tool_calls) if tool_calls else 0,
                "full_message_dict": {
                    "role": "assistant", 
                    "content": msg.content,
                    "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in (tool_calls or [])]
                }
            })

            # If no tool calls, we're done
            if not getattr(msg, "tool_calls", None):
                final_response = {
                    "response": msg.content or "No response generated.",
                    "actions_taken": actions_taken,
                }
                log_to_file(log_file, "conversation_end", {
                    "final_response": final_response,
                    "total_rounds": round_num + 1
                })
                return final_response

            # There are tool calls in this round
            actions_taken = True
            
            # Log tool calls
            log_to_file(log_file, "tool_calls_requested", {
                "round": round_num + 1,
                "tool_calls": [{
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                } for tc in msg.tool_calls]
            })

            # Add the assistant message that requested tools (preserves its reasoning/context)
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [{
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                } for tc in msg.tool_calls],
            })

            # Execute each tool call and append tool results
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                # The API returns a JSON string for arguments; guard against bad JSON
                try:
                    tool_args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    tool_args = {"_raw_args": tc.function.arguments}

                log_to_file(log_file, "tool_execution_start", {
                    "round": round_num + 1,
                    "tool_call_id": tc.id,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "user_context": user_context
                })

                try:
                    result = await execute_mcp_tool(tool_name, tool_args, user_context)

                    # Normalize result to a string for the tool message
                    if isinstance(result, list) and result:
                        first = result[0]
                        if hasattr(first, "text"):
                            result_text = first.text
                        elif isinstance(first, dict) and "text" in first:
                            result_text = first["text"]
                        else:
                            result_text = str(first)
                    else:
                        result_text = str(result)
                    
                    log_to_file(log_file, "tool_execution_success", {
                        "round": round_num + 1,
                        "tool_call_id": tc.id,
                        "tool_name": tool_name,
                        "raw_result": result,
                        "result_text": result_text
                    })

                except Exception as e:
                    result_text = f"Error executing tool '{tool_name}': {e}"
                    
                    log_to_file(log_file, "tool_execution_error", {
                        "round": round_num + 1,
                        "tool_call_id": tc.id,
                        "tool_name": tool_name,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })

                # Log the tool message being added to conversation
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                }
                messages.append(tool_message)
                
                log_to_file(log_file, "tool_message_added", {
                    "round": round_num + 1,
                    "tool_call_id": tc.id,
                    "tool_name": tool_name,
                    "message_added": tool_message
                })
            
            # Log round completion summary
            log_to_file(log_file, "round_completed", {
                "round": round_num + 1,
                "tool_calls_processed": len(tool_calls) if tool_calls else 0,
                "total_messages_in_context": len(messages),
                "continuing_to_next_round": True
            })

        # Safety exit: model kept asking for tools beyond cap
        safety_response = {
            "response": "Stopped due to max_tool_rounds limit; the model kept requesting tools.",
            "actions_taken": actions_taken,
        }
        log_to_file(log_file, "conversation_end_safety", {
            "reason": "max_tool_rounds_exceeded",
            "response": safety_response,
            "total_rounds": max_tool_rounds
        })
        return safety_response

    except Exception as e:
        log_to_file(log_file, "conversation_error", {
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise Exception(f"OpenAI API error: {e}")



async def chat_with_openai_steps(message: str, history: Optional[List[Dict[str, Any]]] = None, model: Optional[str] = None, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Chat interface with OpenAI that returns step-by-step execution details.
    
    Args:
        message: User's current message
        history: Optional conversation history (OpenAI message format)
        model: OpenAI model to use
        
    Returns:
        Dict with 'steps' list and 'final_response' string
    """
    # Use config defaults if not provided
    if model is None:
        model = AI_CONFIG["openai"]["default_model"]
    
    # Create conversation log file
    user_id = user_context.get("user_id", "unknown") if user_context else "unknown"
    log_file = create_conversation_log_file(f"{user_id}_steps")
    
    # Log initial conversation setup
    log_to_file(log_file, "conversation_start_steps", {
        "user_id": user_id,
        "model": model,
        "user_context": user_context,
        "has_history": bool(history)
    })
    
    # Log user message
    log_to_file(log_file, "user_message", {"message": message})
    
    client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    steps = []
    
    # Build messages with history
    if history:
        messages = history.copy()
    else:
        messages = [
            {
                "role": "system", 
                "content": "You are a FastGTD AI assistant. Help users with task management and productivity questions. You have access to tools that can help you provide accurate information. When users ask about the current date or time, use the get_datetime tool to provide accurate, real-time information."
            }
        ]
    
    # Add the current user message
    messages.append({"role": "user", "content": message})
    
    try:
        steps.append("🤔 Analyzing your request...")
        
        # Get MCP tools and convert to OpenAI format
        mcp_manager = await get_mcp_manager()
        mcp_tools = mcp_manager.get_all_tools()
        openai_tools = convert_mcp_tools_to_openai(mcp_tools)
        
        if openai_tools:
            steps.append(f"🔧 Found {len(openai_tools)} available tools")
        
        # OpenAI API call with tools
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=openai_tools if openai_tools else None,
            stream=False
        )
        
        assistant_message = response.choices[0].message
        
        # If no tool calls, return the content
        if not assistant_message.tool_calls:
            steps.append("💬 Generating response...")
            return {
                "steps": steps,
                "final_response": assistant_message.content or "No response generated."
            }
        
        # Process tool calls
        steps.append(f"⚡ Executing {len(assistant_message.tool_calls)} tool(s)...")
        
        tool_messages = messages.copy()
        
        # Add the assistant message with tool calls
        tool_messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [{
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            } for tc in assistant_message.tool_calls]
        })
        
        # Execute each tool call
        for i, tool_call in enumerate(assistant_message.tool_calls):
            try:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                steps.append(f"🔍 Running {tool_name}...")
                
                # Execute the tool via MCP
                tool_result = await execute_mcp_tool(tool_name, tool_args, user_context)
                
                # Convert MCP result to string
                if isinstance(tool_result, list) and len(tool_result) > 0:
                    first_result = tool_result[0]
                    if hasattr(first_result, 'text'):
                        result_text = first_result.text
                    elif isinstance(first_result, dict) and 'text' in first_result:
                        result_text = first_result['text']
                    else:
                        result_text = str(first_result)
                else:
                    result_text = str(tool_result)
                
                steps.append(f"✅ {tool_name} completed")
                
                # Add tool result to messages
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_text
                })
                
            except Exception as e:
                steps.append(f"❌ {tool_name} failed: {str(e)}")
                # Add error result
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"Error executing tool: {str(e)}"
                })
        
        # Get follow-up response from OpenAI
        steps.append("💭 Generating final response...")
        
        follow_up_response = await client.chat.completions.create(
            model=model,
            messages=tool_messages,
            tools=openai_tools if openai_tools else None,
            stream=False
        )
        
        final_response = follow_up_response.choices[0].message.content or "Tool execution completed."
        
        return {
            "steps": steps,
            "final_response": final_response
        }
        
    except Exception as e:
        steps.append(f"❌ Error: {str(e)}")
        return {
            "steps": steps,
            "final_response": f"Sorry, I encountered an error: {str(e)}"
        }


async def chat_with_openai_stream(message: str, history: Optional[List[Dict[str, Any]]] = None, model: Optional[str] = None, user_context: Optional[Dict[str, Any]] = None):
    """
    Streaming chat interface with OpenAI supporting conversation history.
    
    Args:
        message: User's current message
        history: Optional conversation history (OpenAI message format)
        model: OpenAI model to use
        user_context: Optional user context for logging
        
    Yields:
        Streaming chunks of OpenAI's response
    """
    # Use config defaults if not provided
    if model is None:
        model = AI_CONFIG["openai"]["default_model"]
    
    # Create conversation log file
    user_id = user_context.get("user_id", "unknown") if user_context else "unknown"
    log_file = create_conversation_log_file(f"{user_id}_stream")
    
    # Log initial conversation setup
    log_to_file(log_file, "conversation_start_stream", {
        "user_id": user_id,
        "model": model,
        "user_context": user_context,
        "has_history": bool(history)
    })
    
    # Log user message
    log_to_file(log_file, "user_message", {"message": message})
    
    client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Build messages with history
    if history:
        messages = history.copy()
    else:
        messages = [
            {
                "role": "system", 
                "content": "You are a FastGTD AI assistant. Help users with task management and productivity questions. You have access to tools that can help you provide accurate information. When users ask about the current date or time, use the get_datetime tool to provide accurate, real-time information."
            }
        ]
    
    # Add the current user message
    messages.append({"role": "user", "content": message})
    
    try:
        # Streaming OpenAI API call
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
        
    except Exception as e:
        yield f"Error: {e}"