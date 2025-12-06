# src/api/routers/memory.py
"""
Memory router for conversation history management
"""
import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

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
    """Search conversation memory"""
    try:
        memory_manager = MemoryManager(
            vector_store=api_request.app.state.vector_store,
            conversation_db=api_request.app.state.conversation_db
        )
        
        results = await memory_manager.search_conversations(
            query=request.query,
            agent_mode=request.agent_mode,
            limit=request.limit
        )
        
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(api_request: Request, limit: int = 20):
    """List all sessions with preview"""
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
                limit
            )
            sessions = [{
                "session_id": str(r['session_id']),
                "started_at": r['started_at'].isoformat(),
                "last_active": r['last_active'].isoformat(),
                "message_count": r['message_count'],
                "preview": r['first_message'][:50] + "..." if r['first_message'] else "New chat"
            } for r in rows]
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, api_request: Request):
    """Delete a session and all its conversations"""
    try:
        async with api_request.app.state.conversation_db.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM conversations WHERE session_id = $1", session_id)
        return {"status": "deleted", "session_id": session_id, "deleted": True}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# src/api/routers/models.py
"""
Models router for LLM model management
"""
import logging
import os
import ollama
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "agent_configs.yaml"
with open(CONFIG_PATH, 'r') as f:
    CONFIG = yaml.safe_load(f)


@router.get("/list")
async def list_models():
    """List available and installed models"""
    try:
        # Get configured models
        configured_models = CONFIG['models']['available']
        
        # Get installed models from Ollama
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        try:
            installed = ollama.list()
            installed_names = [m['name'] for m in installed.get('models', [])]
        except:
            installed_names = []
        
        # Mark which models are installed
        for model in configured_models:
            model['installed'] = model['name'] in installed_names
        
        return {
            "models": configured_models,
            "default": CONFIG['models']['default']
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PullModelRequest(BaseModel):
    model_name: str


@router.post("/pull")
async def pull_model(request: PullModelRequest):
    """Download a model from Ollama registry"""
    try:
        # Validate model is in configured list
        model_names = [m['name'] for m in CONFIG['models']['available']]
        if request.model_name not in model_names:
            raise HTTPException(status_code=400, detail="Model not in configured list")
        
        # Pull model
        ollama.pull(request.model_name)
        
        return {"status": "success", "model": request.model_name}
    except Exception as e:
        logger.error(f"Error pulling model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{model_name}")
async def delete_model(model_name: str):
    """Delete an installed model"""
    try:
        ollama.delete(model_name)
        return {"status": "deleted", "model": model_name}
    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info/{model_name}")
async def model_info(model_name: str):
    """Get information about a specific model"""
    try:
        info = ollama.show(model_name)
        return {"model": model_name, "info": info}
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=404, detail="Model not found")