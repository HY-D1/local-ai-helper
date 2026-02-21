"""Unit tests for agent system and memory manager."""
import os
import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.agents.agent_controller import AgentController
from src.agents.base_agent import BaseAgent
from src.memory.memory_manager import MemoryManager

os.environ.setdefault("SKIP_MODEL_VALIDATION", "1")


@pytest.mark.asyncio
async def test_base_agent_init():
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
    controller = AgentController()
    assert controller is not None
    agents_info = controller.list_agents()
    assert "general" in agents_info
    assert "math" in agents_info
    assert "code" in agents_info


@pytest.mark.asyncio
async def test_agent_controller_get_agent():
    """Test getting agent from controller."""
    controller = AgentController()
    agent = controller._get_agent("math")
    assert agent.agent_mode == "math"


# Memory manager tests
import pytest
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    store = Mock()
    store.add_conversation = AsyncMock()
    store.search_similar = AsyncMock(return_value=[])
    store.health_check = AsyncMock(return_value=True)
    return store


@pytest.fixture
def mock_conversation_db():
    """Mock conversation database."""
    db = Mock()
    db.store_conversation = AsyncMock()
    db.get_session_conversations = AsyncMock(return_value=[])
    db.health_check = AsyncMock(return_value=True)
    return db


@pytest.fixture
def memory_manager(mock_vector_store, mock_conversation_db):
    """Create memory manager with mocks."""
    return MemoryManager(
        vector_store=mock_vector_store,
        conversation_db=mock_conversation_db,
    )


@pytest.mark.asyncio
async def test_store_conversation(memory_manager, mock_vector_store, mock_conversation_db):
    """Test storing conversation."""
    session_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())

    await memory_manager.store_conversation(
        session_id=session_id,
        conversation_id=conversation_id,
        user_message="Test message",
        assistant_message="Test response",
        agent_mode="general",
        model_used="llama3.2:8b",
    )

    mock_vector_store.add_conversation.assert_called_once()
    mock_conversation_db.store_conversation.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_context(memory_manager, mock_vector_store):
    """Test retrieving context."""
    mock_vector_store.search_similar.return_value = [
        {
            "id": "test_id",
            "text": "Test conversation",
            "metadata": {"session_id": "test_session"},
            "distance": 0.2,
        }
    ]

    results = await memory_manager.retrieve_context(
        query="test query",
        session_id="test_session",
    )

    assert len(results) == 1
    assert results[0]["text"] == "Test conversation"


@pytest.mark.asyncio
async def test_get_session_history(memory_manager, mock_conversation_db):
    """Test getting session history."""
    mock_conversation_db.get_session_conversations.return_value = [
        {
            "id": str(uuid.uuid4()),
            "user_message": "Test",
            "assistant_message": "Response",
            "agent_mode": "general",
            "model_used": "llama3.2:8b",
        }
    ]

    history = await memory_manager.get_session_history("test_session")
    assert len(history) == 1


# Tests for agent with tools
@pytest.mark.asyncio
async def test_agent_with_tools():
    """Test that agent can use tools."""
    agent = BaseAgent(agent_mode="math", enable_tools=True)
    assert agent.tool_registry is not None
    
    # Check that default tools are registered
    tools = agent.tool_registry.list_tools()
    assert "calculator" in tools
    assert "unit_converter" in tools
    assert "code_executor" in tools


@pytest.mark.asyncio
async def test_agent_without_tools():
    """Test that agent can disable tools."""
    agent = BaseAgent(agent_mode="general", enable_tools=False)
    assert agent.tool_registry is None


@pytest.mark.asyncio
async def test_agent_conversation_history():
    """Test conversation history tracking."""
    agent = BaseAgent(agent_mode="general")
    
    # Simulate some conversation
    agent._update_history("Hello", "Hi there!")
    agent._update_history("How are you?", "I'm doing well!")
    
    assert len(agent.conversation_history) == 4  # 2 user + 2 assistant
    assert agent.conversation_history[0]["role"] == "user"
    assert agent.conversation_history[0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_agent_history_limit():
    """Test that conversation history is limited."""
    agent = BaseAgent(agent_mode="general")
    agent.max_history = 2  # Set small limit
    
    # Add more messages than limit
    for i in range(5):
        agent._update_history(f"Message {i}", f"Response {i}")
    
    # Should only keep last 2 exchanges (4 messages)
    assert len(agent.conversation_history) <= 4
