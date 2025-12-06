"""
Unit tests for agent system
"""
import pytest
from src.agents.base_agent import BaseAgent
from src.agents.agent_controller import AgentController


@pytest.mark.asyncio
async def test_base_agent_initialization():
    """Test base agent initialization"""
    agent = BaseAgent(agent_mode='general', model='llama3.2:8b')
    assert agent.agent_mode == 'general'
    assert agent.model == 'llama3.2:8b'
    assert agent.config is not None


@pytest.mark.asyncio
async def test_agent_preprocess():
    """Test message preprocessing"""
    agent = BaseAgent(agent_mode='general')
    message = "Hello, world!"
    processed = await agent.preprocess(message)
    assert processed == message


@pytest.mark.asyncio
async def test_agent_postprocess():
    """Test response postprocessing"""
    agent = BaseAgent(agent_mode='general')
    response = "Response text"
    processed = await agent.postprocess(response)
    assert processed == response


def test_agent_controller_initialization():
    """Test agent controller initialization"""
    controller = AgentController()
    assert controller is not None
    agents_info = controller.list_agents()
    assert 'general' in agents_info
    assert 'math' in agents_info
    assert 'code' in agents_info


@pytest.mark.asyncio
async def test_agent_controller_get_agent():
    """Test getting agent from controller"""
    controller = AgentController()
    agent = controller._get_agent('math')
    assert agent.agent_mode == 'math'


# tests/test_memory.py
"""
Unit tests for memory system
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.memory.memory_manager import MemoryManager
import uuid


@pytest.fixture
def mock_vector_store():
    """Mock vector store"""
    store = Mock()
    store.add_conversation = AsyncMock()
    store.search_similar = AsyncMock(return_value=[])
    store.health_check = AsyncMock(return_value=True)
    return store


@pytest.fixture
def mock_conversation_db():
    """Mock conversation database"""
    db = Mock()
    db.store_conversation = AsyncMock()
    db.get_session_conversations = AsyncMock(return_value=[])
    db.health_check = AsyncMock(return_value=True)
    return db


@pytest.fixture
def memory_manager(mock_vector_store, mock_conversation_db):
    """Create memory manager with mocks"""
    return MemoryManager(
        vector_store=mock_vector_store,
        conversation_db=mock_conversation_db
    )


@pytest.mark.asyncio
async def test_store_conversation(memory_manager, mock_vector_store, mock_conversation_db):
    """Test storing conversation"""
    session_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())
    
    await memory_manager.store_conversation(
        session_id=session_id,
        conversation_id=conversation_id,
        user_message="Test message",
        assistant_message="Test response",
        agent_mode="general",
        model_used="llama3.2:8b"
    )
    
    mock_vector_store.add_conversation.assert_called_once()
    mock_conversation_db.store_conversation.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_context(memory_manager, mock_vector_store):
    """Test retrieving context"""
    mock_vector_store.search_similar.return_value = [
        {
            'id': 'test_id',
            'text': 'Test conversation',
            'metadata': {'session_id': 'test_session'},
            'distance': 0.2
        }
    ]
    
    results = await memory_manager.retrieve_context(
        query="test query",
        session_id="test_session"
    )
    
    assert len(results) == 1
    assert results[0]['text'] == 'Test conversation'


@pytest.mark.asyncio
async def test_get_session_history(memory_manager, mock_conversation_db):
    """Test getting session history"""
    mock_conversation_db.get_session_conversations.return_value = [
        {
            'id': str(uuid.uuid4()),
            'user_message': 'Test',
            'assistant_message': 'Response',
            'agent_mode': 'general',
            'model_used': 'llama3.2:8b'
        }
    ]
    
    history = await memory_manager.get_session_history("test_session")
    assert len(history) == 1