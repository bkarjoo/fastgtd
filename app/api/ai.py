"""AI API endpoints for FastGTD application."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ..ai.openai_handler import chat_with_openai, chat_with_openai_stream, chat_with_openai_steps
import json
from .auth import get_current_user
from ..db.deps import get_db

# In-memory storage for user context (current node)
# TODO: Move to database/Redis for production
user_context_store = {}

router = APIRouter()

class EchoRequest(BaseModel):
    message: str

class EchoResponse(BaseModel):
    response: str
    original_message: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = None
    stream: Optional[bool] = False
    step_by_step: Optional[bool] = False

class ChatResponse(BaseModel):
    response: str
    actions_taken: bool = False

class SetContextRequest(BaseModel):
    current_node_id: Optional[str] = None

class SetContextResponse(BaseModel):
    success: bool
    message: str

class StepResponse(BaseModel):
    steps: List[str]
    final_response: str
    actions_taken: bool = False

@router.post("/echo", response_model=EchoResponse)
async def echo_message(
    request: EchoRequest,
    current_user = Depends(get_current_user)
):
    """
    Echo the provided message back to the user.
    
    Args:
        request: The echo request containing the message
        current_user: The authenticated user
        
    Returns:
        EchoResponse containing the echoed message
    """
    try:
        return EchoResponse(
            response=request.message,
            original_message=request.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Echo service error: {str(e)}")

@router.post("/chat")
async def chat_with_ai(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with OpenAI directly through openai_handler.
    
    Args:
        request: The chat request containing the user's message
        current_user: The authenticated user
        
    Returns:
        ChatResponse containing OpenAI's response
    """
    try:
        print(f"DEBUG: step_by_step = {request.step_by_step}")
        print(f"DEBUG: stream = {request.stream}")
        
        if request.step_by_step:
            # Get stored user context or create basic context
            user_id = str(current_user.id)
            user_context = user_context_store.get(user_id, {
                "user_id": user_id,
                "email": current_user.email
            })
            # Return step-by-step response
            result = await chat_with_openai_steps(request.message, request.history, user_context=user_context)
            return StepResponse(
                steps=result["steps"],
                final_response=result["final_response"]
            )
        elif request.stream:
            # Return streaming response
            async def generate_stream():
                async for chunk in chat_with_openai_stream(request.message, request.history):
                    # Send each chunk as SSE format
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                # Send end marker
                yield "data: {\"done\": true}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # Get stored user context or create basic context
            user_id = str(current_user.id)
            user_context = user_context_store.get(user_id, {
                "user_id": user_id,
                "email": current_user.email
            })
            # Non-streaming response
            result = await chat_with_openai(request.message, request.history, user_context=user_context)
            return ChatResponse(
                response=result["response"],
                actions_taken=result["actions_taken"]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI chat error: {str(e)}")


@router.post("/set-context", response_model=SetContextResponse)
async def set_ai_context(
    request: SetContextRequest,
    current_user = Depends(get_current_user)
):
    """
    Set the AI context (current node) for the user.
    Called by frontend when user opens AI assistant.
    
    Args:
        request: The context request containing current_node_id
        current_user: The authenticated user
        
    Returns:
        SetContextResponse confirming context was set
    """
    try:
        user_id = str(current_user.id)
        
        if request.current_node_id:
            user_context_store[user_id] = {
                "current_node_id": request.current_node_id,
                "user_id": user_id,
                "email": current_user.email
            }
            return SetContextResponse(
                success=True,
                message=f"AI context set to node: {request.current_node_id}"
            )
        else:
            # Clear current node context
            if user_id in user_context_store:
                user_context_store[user_id] = {
                    "user_id": user_id,
                    "email": current_user.email
                }
            return SetContextResponse(
                success=True,
                message="AI context cleared (no current node)"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set AI context: {str(e)}")