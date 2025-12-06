"""
Models router for LLM model management
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import ollama
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.agents.model_selector import select_model

logger = logging.getLogger(__name__)
router = APIRouter()

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

        ollama.pull(request.model_name)
        return {"status": "success", "model": request.model_name}
    except HTTPException:
        raise
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
