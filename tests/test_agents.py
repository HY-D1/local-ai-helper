"""Unit tests for agent behaviors."""

import os

import pytest

# Skip model validation to avoid requiring Ollama models in CI
os.environ["SKIP_MODEL_VALIDATION"] = "1"

from src.agents.agent_controller import AgentController
from src.agents.base_agent import BaseAgent


@pytest.mark.asyncio
async def test_base_agent_initialization():
    """Test base agent initialization."""
    agent = BaseAgent(agent_mode="general", model="llama3.2:8b")
    assert agent.agent_mode == "general"
    assert agent.model == "llama3.2:8b"
    assert agent.config is not None


@pytest.mark.asyncio
async def test_agent_preprocess():
    """Test message preprocessing."""
    agent = BaseAgent(agent_mode="general")
    message = "Hello, world!"
    processed = await agent.preprocess(message)
    assert processed == message


@pytest.mark.asyncio
async def test_agent_postprocess():
    """Test response postprocessing."""
    agent = BaseAgent(agent_mode="general")
    response = "Response text"
    processed = await agent.postprocess(response)
    assert processed == response


def test_agent_controller_initialization():
    """Test agent controller initialization."""
    controller = AgentController(validate_models=False)
    assert controller is not None
    agents_info = controller.list_agents()
    assert "general" in agents_info
    assert "math" in agents_info
    assert "code" in agents_info


@pytest.mark.asyncio
async def test_agent_controller_get_agent():
    """Test getting agent from controller."""
    controller = AgentController(validate_models=False)
    agent = controller._get_agent("math")
    assert agent.agent_mode == "math"
