"""Model selection utilities for choosing optimal Ollama models."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterable, List, Optional

import ollama

logger = logging.getLogger(__name__)

# Order models by perceived quality. Higher scores mean higher preference.
QUALITY_SCORES = {
    "excellent": 4,
    "excellent (code)": 4,
    "very good": 3,
    "good": 2,
    "ok": 1,
}


def _parse_quality(quality: str) -> int:
    """Convert a human-friendly quality string into a numeric score."""
    if not quality:
        return 0
    quality_lower = quality.strip().lower()
    for label, score in QUALITY_SCORES.items():
        if label in quality_lower:
            return score
    return 0


def _parse_size_gb(size: Optional[str]) -> float:
    """Parse a size string like '4.7 GB' into a float representing GB."""
    if not size:
        return 0.0
    try:
        return float(size.split()[0])
    except Exception:
        return 0.0


def get_installed_models() -> List[str]:
    """Return the list of installed model names, handling offline scenarios gracefully."""
    if os.getenv("SKIP_MODEL_VALIDATION"):
        return []

    try:
        installed = ollama.list()
        return [model.get("name") for model in installed.get("models", []) if model.get("name")]
    except Exception as exc:  # pragma: no cover - defensive guard for runtime issues
        logger.warning("Unable to list installed models: %s", exc)
        return []


def _best_installed_model(
    available_models: Iterable[Dict[str, Any]], installed_models: Iterable[str]
) -> Optional[str]:
    """Pick the highest quality installed model from the configured list."""
    installed_set = set(installed_models)
    candidates = []
    for model in available_models:
        name = model.get("name")
        if not name or name not in installed_set:
            continue
        quality_score = _parse_quality(model.get("quality", ""))
        size_score = _parse_size_gb(model.get("size"))
        # Larger models typically perform better when quality is equal.
        candidates.append((quality_score, size_score, name))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][2]


def select_model(
    preferred_model: str,
    models_config: Dict[str, Any],
    *,
    installed_models: Optional[Iterable[str]] = None,
    allow_best_installed_fallback: bool = True,
) -> str:
    """Choose the optimal model based on configuration and installed availability.

    Args:
        preferred_model: Requested model name.
        models_config: Models configuration mapping from the YAML file.
        installed_models: Optional injected list for testing; defaults to live Ollama list.
        allow_best_installed_fallback: Whether to fall back to the best installed model
            when the preferred option is unavailable.

    Returns:
        Selected model name.

    Raises:
        ValueError: If no suitable model can be selected.
    """
    available_models = models_config.get("available", [])
    available_names = [model.get("name") for model in available_models if model.get("name")]

    # Prefer the requested model when provided, even if it's not listed in the catalog.
    # Fall back to configured defaults when no preference is supplied.
    target_model = preferred_model or models_config.get("default")
    if not target_model and available_names:
        target_model = available_names[0]

    if not target_model:
        raise ValueError("No models are configured for selection.")

    skip_validation = bool(os.getenv("SKIP_MODEL_VALIDATION"))

    if skip_validation:
        return target_model

    installed = list(installed_models) if installed_models is not None else get_installed_models()

    if not installed:
        return target_model

    if target_model in installed:
        return target_model

    if allow_best_installed_fallback:
        best_installed = _best_installed_model(available_models, installed)
        if best_installed:
            logger.info("Falling back to installed model '%s'", best_installed)
            return best_installed

    raise ValueError(
        f"Model '{target_model}' not installed. Please download it first or choose an installed model."
    )
