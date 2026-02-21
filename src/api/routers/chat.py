"""Chat router for handling conversation endpoints."""
import json
import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agents.agent_controller import AgentController
from src.memory.enhanced_memory_manager import EnhancedMemoryManager

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    agent_mode: str = Field("general", description="Agent mode (general, math, code, writing, design)")
    model: Optional[str] = Field(None, description="Model to use (defaults to configured model)")
    use_memory: bool = Field(True, description="Whether to use conversation memory")
    use_hybrid_search: bool = Field(True, description="Use hybrid search for better retrieval")
    use_context_compression: bool = Field(True, description="Compress long conversation history")
    stream: bool = Field(False, description="Stream response")
    temperature: Optional[float] = Field(0.7, description="Generation temperature (0-1)")
    max_tokens: Optional[int] = Field(512, description="Max response tokens")


class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_mode: str
    model_used: str
    conversation_id: str
    context_info: Optional[dict] = None


@router.post("/completion", response_model=ChatResponse)
async def chat_completion(request: ChatRequest, api_request: Request):
    """Generate a chat completion."""
    try:
        session_id = request.session_id or str(uuid4())
        agent_controller = AgentController()
        
        # Use enhanced memory manager
        memory_manager = EnhancedMemoryManager(
            vector_store=api_request.app.state.vector_store,
            conversation_db=api_request.app.state.conversation_db,
            use_hybrid_search=request.use_hybrid_search,
            use_context_compression=request.use_context_compression,
        )

        # Retrieve enhanced context
        context_info = None
        context = ""
        if request.use_memory:
            context_result = await memory_manager.get_enhanced_context(
                query=request.message,
                session_id=session_id,
                current_message=request.message,
                max_chunks=5,
                max_tokens=3000,  # Leave room for response
            )
            context = context_result["context"]
            context_info = {
                "semantic_results": context_result.get("semantic_results", 0),
                "history_turns": context_result.get("history_turns", 0),
                "summarized": context_result.get("summarized", 0),
                "estimated_tokens": context_result.get("estimated_tokens", 0),
            }
            logger.info(
                "Context retrieved: %d semantic, %d history turns, %d summarized",
                context_info["semantic_results"],
                context_info["history_turns"],
                context_info["summarized"],
            )

        response = await agent_controller.generate(
            message=request.message,
            agent_mode=request.agent_mode,
            model=request.model,
            context=context,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        conversation_id = str(uuid4())
        if request.use_memory:
            await memory_manager.store_conversation(
                session_id=session_id,
                conversation_id=conversation_id,
                user_message=request.message,
                assistant_message=response["response"],
                agent_mode=request.agent_mode,
                model_used=response["model_used"],
            )

        return ChatResponse(
            response=response["response"],
            session_id=session_id,
            agent_mode=request.agent_mode,
            model_used=response["model_used"],
            conversation_id=conversation_id,
            context_info=context_info,
        )

    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest, api_request: Request):
    """Stream a chat completion."""
    try:
        session_id = request.session_id or str(uuid4())
        agent_controller = AgentController()
        
        # Use enhanced memory manager
        memory_manager = EnhancedMemoryManager(
            vector_store=api_request.app.state.vector_store,
            conversation_db=api_request.app.state.conversation_db,
            use_hybrid_search=request.use_hybrid_search,
            use_context_compression=request.use_context_compression,
        )

        # Retrieve enhanced context
        context = ""
        if request.use_memory:
            context_result = await memory_manager.get_enhanced_context(
                query=request.message,
                session_id=session_id,
                current_message=request.message,
                max_chunks=5,
                max_tokens=3000,
            )
            context = context_result["context"]

        async def generate_stream():
            full_response = ""
            conversation_id = str(uuid4())
            model_used = request.model or ""

            try:
                async for chunk in agent_controller.generate_stream(
                    message=request.message,
                    agent_mode=request.agent_mode,
                    model=request.model,
                    context=context,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                ):
                    text_chunk = chunk.get("text", "")
                    if not model_used:
                        model_used = chunk.get("model_used", "")
                    full_response += text_chunk
                    yield f"data: {json.dumps({'text': text_chunk, 'done': False})}\n\n"
            except Exception as exc:  # noqa: BLE001
                logger.error("Stream generation failed: %s", exc)
                yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"
                return

            model_used = model_used or request.model or "unknown"

            if request.use_memory and full_response:
                await memory_manager.store_conversation(
                    session_id=session_id,
                    conversation_id=conversation_id,
                    user_message=request.message,
                    assistant_message=full_response,
                    agent_mode=request.agent_mode,
                    model_used=model_used,
                )

            yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'conversation_id': conversation_id, 'model_used': model_used})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
        )

    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, api_request: Request, limit: int = 50):
    """Get conversation history for a session."""
    try:
        conversations = await api_request.app.state.conversation_db.get_session_conversations(
            session_id=session_id,
            limit=limit,
        )
        return {"session_id": session_id, "conversations": conversations}
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/summarize")
async def summarize_session(session_id: str, api_request: Request):
    """Generate a summary of a conversation session."""
    try:
        # Get all conversations for the session
        conversations = await api_request.app.state.conversation_db.get_session_conversations(
            session_id=session_id,
            limit=1000,
        )
        
        if not conversations:
            return {"session_id": session_id, "summary": "No conversations found."}
        
        # Create a simple summary (in production, use LLM for this)
        topics = []
        for conv in conversations:
            msg = conv.get("user_message", "")
            if msg:
                # Extract first sentence or first 50 chars
                preview = msg.split(".")[0][:50] if "." in msg else msg[:50]
                topics.append(preview)
        
        summary = f"Session with {len(conversations)} exchanges. Topics: " + " | ".join(topics[:5])
        
        return {
            "session_id": session_id,
            "summary": summary,
            "total_conversations": len(conversations),
            "topics": topics[:10],
        }
    except Exception as e:
        logger.error(f"Error summarizing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
