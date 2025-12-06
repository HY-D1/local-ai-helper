"""
Chat router for handling chat completions and streaming
"""
import logging
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from src.agents.agent_controller import AgentController
from src.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    agent_mode: str = Field("general", description="Agent mode (general, math, code, writing, design)")
    model: Optional[str] = Field(None, description="Model to use (defaults to configured model)")
    use_memory: bool = Field(True, description="Whether to use conversation memory")
    stream: bool = Field(False, description="Stream response")
    temperature: Optional[float] = Field(0.7, description="Generation temperature (0-1)")
    max_tokens: Optional[int] = Field(512, description="Max response tokens")


class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_mode: str
    model_used: str
    conversation_id: str


@router.post("/completion", response_model=ChatResponse)
async def chat_completion(request: ChatRequest, api_request: Request):
    """
    Generate a chat completion
    """
    try:
        # Initialize session if not provided
        session_id = request.session_id or str(uuid4())
        
        # Initialize agent controller
        agent_controller = AgentController()
        
        # Initialize memory manager
        memory_manager = MemoryManager(
            vector_store=api_request.app.state.vector_store,
            conversation_db=api_request.app.state.conversation_db
        )
        
        # Retrieve relevant context from memory if enabled
        context = ""
        if request.use_memory:
            context_chunks = await memory_manager.retrieve_context(
                query=request.message,
                session_id=session_id,
                max_chunks=5
            )
            context = "\n".join([chunk['text'] for chunk in context_chunks])
            logger.info(f"Context retrieved: {len(context_chunks)} chunks, {len(context)} chars")
            if context:
                logger.info(f"Context preview: {context[:100]}...")
        
        # Generate response
        response = await agent_controller.generate(
            message=request.message,
            agent_mode=request.agent_mode,
            model=request.model,
            context=context,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Store conversation in memory
        conversation_id = str(uuid4())
        if request.use_memory:
            await memory_manager.store_conversation(
                session_id=session_id,
                conversation_id=conversation_id,
                user_message=request.message,
                assistant_message=response['response'],
                agent_mode=request.agent_mode,
                model_used=response['model_used']
            )
        
        return ChatResponse(
            response=response['response'],
            session_id=session_id,
            agent_mode=request.agent_mode,
            model_used=response['model_used'],
            conversation_id=conversation_id
        )
        
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest, api_request: Request):
    """
    Stream a chat completion
    """
    try:
        session_id = request.session_id or str(uuid4())
        agent_controller = AgentController()
        memory_manager = MemoryManager(
            vector_store=api_request.app.state.vector_store,
            conversation_db=api_request.app.state.conversation_db
        )
        
        # Retrieve context
        context = ""
        if request.use_memory:
            context_chunks = await memory_manager.retrieve_context(
                query=request.message,
                session_id=session_id,
                max_chunks=5
            )
            context = "\n".join([chunk['text'] for chunk in context_chunks])
        
        async def generate_stream():
            full_response = ""
            conversation_id = str(uuid4())
            
            async for chunk in agent_controller.generate_stream(
                message=request.message,
                agent_mode=request.agent_mode,
                model=request.model,
                context=context
            ):
                full_response += chunk['text']
                yield f"data: {json.dumps(chunk)}\n\n"
            
            # Store complete conversation
            if request.use_memory:
                await memory_manager.store_conversation(
                    session_id=session_id,
                    conversation_id=conversation_id,
                    user_message=request.message,
                    assistant_message=full_response,
                    agent_mode=request.agent_mode,
                    model_used=chunk.get('model_used', 'unknown')
                )
            
            # Send final metadata
            yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'conversation_id': conversation_id})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, api_request: Request, limit: int = 50):
    """
    Get conversation history for a session
    """
    try:
        conversations = await api_request.app.state.conversation_db.get_session_conversations(
            session_id=session_id,
            limit=limit
        )
        return {"session_id": session_id, "conversations": conversations}
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=str(e))