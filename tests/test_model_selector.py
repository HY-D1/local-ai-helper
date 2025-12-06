"""Tests for the model selector utilities."""
import os
from pathlib import Path

import pytest
import yaml

from src.agents.model_selector import select_model

CONFIG = yaml.safe_load((Path(__file__).parents[1] / "config" / "agent_configs.yaml").read_text())


@pytest.fixture(autouse=True)
def clear_skip_flag(monkeypatch):
    monkeypatch.delenv("SKIP_MODEL_VALIDATION", raising=False)
    yield
    monkeypatch.delenv("SKIP_MODEL_VALIDATION", raising=False)


def test_select_model_prefers_installed_default(monkeypatch):
    models_config = CONFIG["models"]
    result = select_model(
        "llama3.2:8b",
        models_config,
        installed_models=["llama3.2:8b", "llama3.2:3b"],
    )
    assert result == "llama3.2:8b"


def test_select_model_falls_back_to_best_quality(monkeypatch):
    models_config = CONFIG["models"]
    result = select_model(
        "nonexistent-model",
        models_config,
        installed_models=["llama3.2:3b", "qwen2.5:7b"],
    )
    assert result == "qwen2.5:7b"


def test_select_model_respects_skip_validation(monkeypatch):
    models_config = CONFIG["models"]
    monkeypatch.setenv("SKIP_MODEL_VALIDATION", "1")
    result = select_model(
        "custom-large-model",
        models_config,
        installed_models=[],
    )
    # When validation is skipped we return the target without checking installation.
    assert result == "custom-large-model"
