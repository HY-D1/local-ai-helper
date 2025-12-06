"""
Models router for LLM model management.
"""

import logging
from pathlib import Path
from typing import List

import ollama
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "agent_configs.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)


@router.get("/list")
async def list_models():
    """List available and installed models."""
    try:
        configured_models: List[dict] = CONFIG["models"]["available"]

        try:
            installed = ollama.list()
            installed_names = [model_info["name"] for model_info in installed.get("models", [])]
        except Exception as exc:  # noqa: BLE001 - surface ollama errors gracefully
            logger.warning("Unable to list installed models: %s", exc)
            installed_names = []

        for model in configured_models:
            model["installed"] = model["name"] in installed_names

        return {
            "models": configured_models,
            "default": CONFIG["models"]["default"],
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("Error listing models: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class PullModelRequest(BaseModel):
    model_name: str


@router.post("/pull")
async def pull_model(request: PullModelRequest):
    """Download a model from the Ollama registry."""
    try:
        model_names = [model["name"] for model in CONFIG["models"]["available"]]
        if request.model_name not in model_names:
            raise HTTPException(status_code=400, detail="Model not in configured list")

        ollama.pull(request.model_name)
        return {"status": "success", "model": request.model_name}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Error pulling model: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/delete/{model_name}")
async def delete_model(model_name: str):
    """Delete an installed model."""
    try:
        ollama.delete(model_name)
        return {"status": "deleted", "model": model_name}
    except Exception as exc:  # noqa: BLE001
        logger.error("Error deleting model: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/info/{model_name}")
async def model_info(model_name: str):
    """Get information about a specific model."""
    try:
        info = ollama.show(model_name)
        return {"model": model_name, "info": info}
    except Exception as exc:  # noqa: BLE001
        logger.error("Error getting model info: %s", exc)
        raise HTTPException(status_code=404, detail="Model not found") from exc
