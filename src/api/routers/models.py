"""
Models router for LLM model management
"""
import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any

import ollama
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.agents.model_selector import select_model

logger = logging.getLogger(__name__)
router = APIRouter()

TASKS: Dict[str, Dict[str, Any]] = {}

CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "agent_configs.yaml"
with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)


@router.get("/list")
async def list_models():
    """List available and installed models"""
    try:
        configured_models = CONFIG["models"]["available"]

        # Get installed models from Ollama
        try:
            installed = ollama.list()
            installed_names = [m["name"] for m in installed.get("models", [])]
        except Exception:
            installed_names = []

        # Mark which models are installed
        models: List[Dict[str, Any]] = []
        for model in configured_models:
            model_copy = dict(model)
            model_copy["installed"] = model["name"] in installed_names
            models.append(model_copy)

        try:
            recommended = select_model(
                CONFIG["models"].get("default", ""),
                CONFIG["models"],
                installed_models=installed_names,
            )
        except Exception:
            recommended = CONFIG["models"].get("default")

        return {
            "models": models,
            "default": CONFIG["models"]["default"],
            "recommended": recommended,
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
        model_names = [m["name"] for m in CONFIG["models"]["available"]]
        if request.model_name not in model_names:
            raise HTTPException(status_code=400, detail="Model not in configured list")

        task_id = str(uuid.uuid4())
        TASKS[task_id] = {"status": "in_progress", "model": request.model_name, "action": "pull"}

        async def run_pull():
            try:
                await asyncio.get_running_loop().run_in_executor(
                    None, lambda: ollama.pull(request.model_name)
                )
                TASKS[task_id].update({"status": "completed"})
            except Exception as exc:  # pragma: no cover - network/ollama dependent
                TASKS[task_id].update({"status": "error", "detail": str(exc)})

        asyncio.create_task(run_pull())

        return {"status": "in_progress", "task_id": task_id, "model": request.model_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pulling model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{model_name}")
async def delete_model(model_name: str):
    """Delete an installed model"""
    try:
        task_id = str(uuid.uuid4())
        TASKS[task_id] = {"status": "in_progress", "model": model_name, "action": "delete"}

        async def run_delete():
            try:
                await asyncio.get_running_loop().run_in_executor(
                    None, lambda: ollama.delete(model_name)
                )
                TASKS[task_id].update({"status": "completed"})
            except Exception as exc:  # pragma: no cover - network/ollama dependent
                TASKS[task_id].update({"status": "error", "detail": str(exc)})

        asyncio.create_task(run_delete())

        return {"status": "in_progress", "task_id": task_id, "model": model_name}
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


@router.get("/tasks/{task_id}")
async def task_status(task_id: str):
    """Fetch status for long-running model operations"""
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
