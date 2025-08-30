"""
OpenAI handler for FastGTD application.
Simple message-in, message-out interface without streaming or tools for now.
"""

import openai
import os
import json
from typing import List, Dict, Any, Optional
from .fastmcp_manager import get_mcp_manager, execute_mcp_tool


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
    model: str = "gpt-4o-mini",
    user_context: Optional[Dict[str, Any]] = None,
    max_tool_rounds: int = 5,  # safety cap to prevent infinite loops
) -> Dict[str, Any]:
    """
    Multi-hop tool-calling chat interface:
    Repeatedly calls OpenAI; if the model requests tools, execute them,
    append results, and ask the model again—until no more tool calls.
    """
    client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        mcp_manager = await get_mcp_manager()
        mcp_tools = mcp_manager.get_all_tools()
        openai_tools = convert_mcp_tools_to_openai(mcp_tools)
        actions_taken = False

        # Multi-round loop
        for _ in range(max_tool_rounds):
            # Ask the model
            resp = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                stream=False,
            )
            msg = resp.choices[0].message

            # If no tool calls, we're done
            if not getattr(msg, "tool_calls", None):
                return {
                    "response": msg.content or "No response generated.",
                    "actions_taken": actions_taken,
                }

            # There are tool calls in this round
            actions_taken = True

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

                except Exception as e:
                    result_text = f"Error executing tool '{tool_name}': {e}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                })

        # Safety exit: model kept asking for tools beyond cap
        return {
            "response": "Stopped due to max_tool_rounds limit; the model kept requesting tools.",
            "actions_taken": actions_taken,
        }

    except Exception as e:
        raise Exception(f"OpenAI API error: {e}")



async def chat_with_openai_steps(message: str, history: Optional[List[Dict[str, Any]]] = None, model: str = "gpt-4o-mini", user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Chat interface with OpenAI that returns step-by-step execution details.
    
    Args:
        message: User's current message
        history: Optional conversation history (OpenAI message format)
        model: OpenAI model to use
        
    Returns:
        Dict with 'steps' list and 'final_response' string
    """
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


async def chat_with_openai_stream(message: str, history: Optional[List[Dict[str, Any]]] = None, model: str = "gpt-4o-mini"):
    """
    Streaming chat interface with OpenAI supporting conversation history.
    
    Args:
        message: User's current message
        history: Optional conversation history (OpenAI message format)
        model: OpenAI model to use
        
    Yields:
        Streaming chunks of OpenAI's response
    """
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