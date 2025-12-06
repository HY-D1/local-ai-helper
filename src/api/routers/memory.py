"""
Memory router for conversation history management.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    agent_mode: Optional[str] = None
    limit: int = 20


@router.post("/search")
async def search_memory(request: SearchRequest, api_request: Request):
    """Search conversation memory."""
    try:
        memory_manager = MemoryManager(
            vector_store=api_request.app.state.vector_store,
            conversation_db=api_request.app.state.conversation_db,
        )

        results = await memory_manager.search_conversations(
            query=request.query,
            agent_mode=request.agent_mode,
            limit=request.limit,
        )

        return {"results": results, "count": len(results)}
    except Exception as exc:  # noqa: BLE001
        logger.error("Search error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions")
async def list_sessions(api_request: Request, limit: int = 20):
    """List all sessions with preview."""
    try:
        async with api_request.app.state.conversation_db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    c.session_id,
                    MIN(c.created_at) as started_at,
                    MAX(c.created_at) as last_active,
                    COUNT(*) as message_count,
                    (SELECT user_message FROM conversations WHERE session_id = c.session_id ORDER BY created_at LIMIT 1) as first_message
                FROM conversations c
                GROUP BY c.session_id
                ORDER BY MAX(c.created_at) DESC
                LIMIT $1
                """,
                limit,
            )
            sessions = [
                {
                    "session_id": str(row["session_id"]),
                    "started_at": row["started_at"].isoformat(),
                    "last_active": row["last_active"].isoformat(),
                    "message_count": row["message_count"],
                    "preview": f"{row['first_message'][:50]}..." if row["first_message"] else "New chat",
                }
                for row in rows
            ]
        return {"sessions": sessions}
    except Exception as exc:  # noqa: BLE001
        logger.error("Error listing sessions: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, api_request: Request):
    """Delete a session and all its conversations."""
    try:
        async with api_request.app.state.conversation_db.pool.acquire() as conn:
            await conn.execute("DELETE FROM conversations WHERE session_id = $1", session_id)
        return {"status": "deleted", "session_id": session_id, "deleted": True}
    except Exception as exc:  # noqa: BLE001
        logger.error("Error deleting session: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
