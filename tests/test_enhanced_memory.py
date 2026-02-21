"""Tests for enhanced memory manager."""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.memory.enhanced_memory_manager import EnhancedMemoryManager


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
def enhanced_memory_manager(mock_vector_store, mock_conversation_db):
    return EnhancedMemoryManager(
        vector_store=mock_vector_store,
        conversation_db=mock_conversation_db,
        use_hybrid_search=True,
        use_context_compression=True,
    )


class TestEnhancedMemoryManager:
    """Tests for enhanced memory manager."""
    
    @pytest.mark.asyncio
    async def test_init(self, enhanced_memory_manager):
        assert enhanced_memory_manager.use_hybrid_search is True
        assert enhanced_memory_manager.use_context_compression is True
        assert enhanced_memory_manager.hybrid_searcher is not None
        assert enhanced_memory_manager.context_compressor is not None
        
    @pytest.mark.asyncio
    async def test_retrieve_context_hybrid_disabled(self, mock_vector_store, mock_conversation_db):
        manager = EnhancedMemoryManager(
            vector_store=mock_vector_store,
            conversation_db=mock_conversation_db,
            use_hybrid_search=False,
        )
        
        mock_vector_store.search_similar.return_value = [
            {"id": "doc1", "text": "test", "distance": 0.1}
        ]
        
        results = await manager.retrieve_context_hybrid("query", "session1")
        assert len(results) == 1
        
    @pytest.mark.asyncio
    async def test_get_compressed_context_disabled(self, mock_vector_store, mock_conversation_db):
        manager = EnhancedMemoryManager(
            vector_store=mock_vector_store,
            conversation_db=mock_conversation_db,
            use_context_compression=False,
        )
        
        mock_conversation_db.get_session_conversations.return_value = [
            {"user_message": "Hello", "assistant_message": "Hi!"}
        ]
        
        result = await manager.get_compressed_context("session1", "test")
        assert "context" in result
        assert result["summarized"] == 0
        
    @pytest.mark.asyncio
    async def test_get_enhanced_context(self, enhanced_memory_manager, mock_vector_store):
        mock_vector_store.search_similar.return_value = [
            {"id": "doc1", "text": "Relevant context", "distance": 0.1}
        ]
        
        result = await enhanced_memory_manager.get_enhanced_context(
            query="test query",
            session_id="session1",
            current_message="current message",
        )
        
        assert "context" in result
        assert "semantic_results" in result
        assert "history_turns" in result
        
    @pytest.mark.asyncio
    async def test_get_enhanced_context_empty(self, enhanced_memory_manager):
        result = await enhanced_memory_manager.get_enhanced_context(
            query="test",
            session_id=None,
            current_message="test",
        )
        
        assert result["context"] == ""
        assert result["semantic_results"] == 0
        
    def test_format_history_as_context(self, enhanced_memory_manager):
        history = [
            {"user_message": "Hello", "assistant_message": "Hi!"},
            {"user_message": "How are you?", "assistant_message": "Good!"},
        ]
        context = enhanced_memory_manager._format_history_as_context(history)
        assert "Hello" in context
        assert "Hi!" in context
        assert "How are you?" in context
        
    @pytest.mark.asyncio
    async def test_build_bm25_index(self, enhanced_memory_manager, mock_conversation_db):
        mock_conversation_db.get_session_conversations.return_value = [
            {
                "id": "conv1",
                "user_message": "Hello world",
                "assistant_message": "Hi there",
                "session_id": "session1",
            }
        ]
        
        await enhanced_memory_manager._build_bm25_index("session1")
        
        assert "conv1" in enhanced_memory_manager._bm25_index
        
    @pytest.mark.asyncio
    async def test_retrieve_context_hybrid_with_data(
        self, 
        enhanced_memory_manager, 
        mock_vector_store, 
        mock_conversation_db
    ):
        # Setup vector store results
        mock_vector_store.search_similar.return_value = [
            {"id": "doc1", "text": "Vector result", "distance": 0.1, "metadata": {}}
        ]
        
        # Setup DB results for BM25 index
        mock_conversation_db.get_session_conversations.return_value = [
            {
                "id": "doc1",
                "user_message": "Hello",
                "assistant_message": "Hi",
                "created_at": "2024-01-01",
            }
        ]
        
        results = await enhanced_memory_manager.retrieve_context_hybrid("hello", "session1")
        
        # Should have results from both sources
        assert isinstance(results, list)
        
    @pytest.mark.asyncio
    async def test_retrieve_context_hybrid_error_fallback(
        self,
        enhanced_memory_manager,
        mock_vector_store,
    ):
        # Make vector store raise error
        mock_vector_store.search_similar.side_effect = Exception("DB error")
        
        # Should fallback to standard retrieval, which also fails
        # But catches the exception and returns empty list
        results = await enhanced_memory_manager.retrieve_context_hybrid("query")
        assert results == []  # Returns empty list on error
