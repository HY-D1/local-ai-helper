"""Unit tests for memory system."""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from src.memory.memory_manager import MemoryManager


@pytest.fixture
def mock_vector_store():
    store = Mock()
    store.add_conversation = AsyncMock()
    store.search_similar = AsyncMock(return_value=[])
    store.health_check = AsyncMock(return_value=True)
    return store


@pytest.fixture
def mock_conversation_db():
    db = Mock()
    db.store_conversation = AsyncMock()
    db.get_session_conversations = AsyncMock(return_value=[])
    db.health_check = AsyncMock(return_value=True)
    return db


@pytest.fixture
def memory_manager(mock_vector_store, mock_conversation_db):
    return MemoryManager(
        vector_store=mock_vector_store,
        conversation_db=mock_conversation_db,
    )


@pytest.mark.asyncio
async def test_store_conversation(memory_manager, mock_vector_store, mock_conversation_db):
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
