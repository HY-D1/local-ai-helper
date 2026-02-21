"""
Enhanced Memory Manager with hybrid search and context compression.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.memory.memory_manager import MemoryManager
from src.memory.hybrid_search import HybridSearcher
from src.memory.context_compressor import ContextCompressor, ConversationTurn

logger = logging.getLogger(__name__)


class EnhancedMemoryManager(MemoryManager):
    """
    Extended memory manager with advanced retrieval features:
    - Hybrid search (semantic + keyword)
    - Context compression for long conversations
    - Re-ranking of results
    """
    
    def __init__(
        self,
        vector_store,
        conversation_db,
        use_hybrid_search: bool = True,
        use_context_compression: bool = True,
    ):
        super().__init__(vector_store, conversation_db)
        self.use_hybrid_search = use_hybrid_search
        self.use_context_compression = use_context_compression
        
        # Initialize hybrid searcher
        self.hybrid_searcher = HybridSearcher(
            vector_weight=0.7,
            keyword_weight=0.3,
        ) if use_hybrid_search else None
        
        # Initialize context compressor
        self.context_compressor = ContextCompressor(
            max_tokens=4096,
            preserve_recent=4,
        ) if use_context_compression else None
        
        # BM25 index for hybrid search
        self._bm25_index: Dict[str, Any] = {}
        
    async def _build_bm25_index(self, session_id: Optional[str] = None):
        """Build BM25 index from stored conversations."""
        if not self.hybrid_searcher:
            return
            
        try:
            # Get conversations from database
            conversations = await self.conversation_db.get_session_conversations(
                session_id=session_id or "",
                limit=1000,
            )
            
            # Add to BM25 index
            for conv in conversations:
                doc_id = conv.get("id", str(conv.get("created_at", "")))
                text = f"{conv.get('user_message', '')} {conv.get('assistant_message', '')}"
                self.hybrid_searcher.bm25.add_document(doc_id, text)
                self._bm25_index[doc_id] = conv
                
            logger.info(f"Built BM25 index with {len(conversations)} documents")
        except Exception as e:
            logger.error(f"Error building BM25 index: {e}")
            
    async def retrieve_context_hybrid(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_chunks: int = 5,
        similarity_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context using hybrid search (vector + keyword).
        
        Args:
            query: Search query
            session_id: Optional session filter
            max_chunks: Maximum results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of relevant context chunks
        """
        if not self.use_hybrid_search or not self.hybrid_searcher:
            # Fall back to standard retrieval
            return await self.retrieve_context(
                query=query,
                session_id=session_id,
                max_chunks=max_chunks,
                similarity_threshold=similarity_threshold,
            )
            
        try:
            # Ensure BM25 index is built
            if not self._bm25_index:
                await self._build_bm25_index(session_id)
                
            # Vector search
            filter_metadata = {"session_id": session_id} if session_id else None
            vector_results = await self.vector_store.search_similar(
                query=query,
                max_results=max_chunks * 2,
                filter_metadata=filter_metadata,
            )
            
            # Keyword search
            keyword_results = self.hybrid_searcher.bm25.search(query, top_k=max_chunks * 2)
            
            # Enrich keyword results with full data
            for result in keyword_results:
                doc_id = result["id"]
                if doc_id in self._bm25_index:
                    conv = self._bm25_index[doc_id]
                    result["metadata"] = {
                        "session_id": conv.get("session_id"),
                        "agent_mode": conv.get("agent_mode"),
                        "model_used": conv.get("model_used"),
                        "timestamp": conv.get("created_at"),
                    }
                    
            # Combine results
            combined = self.hybrid_searcher.combine_results(
                vector_results=vector_results,
                keyword_results=keyword_results,
                top_k=max_chunks,
            )
            
            # Filter by threshold
            filtered = [
                r for r in combined 
                if r.get("hybrid_score", 0) >= similarity_threshold
            ]
            
            logger.info(
                f"Hybrid search: {len(vector_results)} vector + {len(keyword_results)} keyword = {len(combined)} combined, {len(filtered)} after threshold"
            )
            
            return filtered if filtered else combined[:max_chunks]
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            # Fall back to standard retrieval
            return await self.retrieve_context(
                query=query,
                session_id=session_id,
                max_chunks=max_chunks,
                similarity_threshold=similarity_threshold,
            )
            
    async def get_compressed_context(
        self,
        session_id: str,
        current_message: str,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Get compressed conversation context for the session.
        
        Args:
            session_id: Session ID
            current_message: Current user message
            max_tokens: Maximum tokens for context
            
        Returns:
            Compressed context and metadata
        """
        if not self.use_context_compression or not self.context_compressor:
            # Fall back to standard history
            history = await self.get_session_history(session_id)
            return {
                "context": self._format_history_as_context(history),
                "turns_included": len(history),
                "summarized": 0,
            }
            
        try:
            # Get conversation history
            history = await self.get_session_history(session_id)
            
            if not history:
                return {"context": "", "turns_included": 0, "summarized": 0}
                
            # Convert to ConversationTurn objects
            turns = []
            for conv in reversed(history):  # Oldest first
                turns.append(ConversationTurn(
                    role="user",
                    content=conv.get("user_message", ""),
                    timestamp=conv.get("created_at"),
                ))
                turns.append(ConversationTurn(
                    role="assistant",
                    content=conv.get("assistant_message", ""),
                    timestamp=conv.get("created_at"),
                ))
                
            # Compress context
            self.context_compressor.max_tokens = max_tokens
            result = self.context_compressor.compress(turns, current_message)
            
            return result
            
        except Exception as e:
            logger.error(f"Context compression error: {e}")
            history = await self.get_session_history(session_id)
            return {
                "context": self._format_history_as_context(history),
                "turns_included": len(history),
                "summarized": 0,
            }
            
    def _format_history_as_context(self, history: List[Dict[str, Any]]) -> str:
        """Format history as context string."""
        parts = []
        for conv in reversed(history):
            parts.append(f"User: {conv.get('user_message', '')}")
            parts.append(f"Assistant: {conv.get('assistant_message', '')}")
        return "\n".join(parts)
        
    async def get_enhanced_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        current_message: str = "",
        max_chunks: int = 5,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Get enhanced context combining hybrid search and compression.
        
        Args:
            query: Search query for semantic retrieval
            session_id: Session ID
            current_message: Current user message
            max_chunks: Maximum semantic chunks to retrieve
            max_tokens: Maximum tokens for context
            
        Returns:
            Enhanced context with metadata
        """
        # Get hybrid search results
        semantic_results = await self.retrieve_context_hybrid(
            query=query,
            session_id=session_id,
            max_chunks=max_chunks,
        )
        
        # Get compressed conversation history
        compressed = await self.get_compressed_context(
            session_id=session_id or "",
            current_message=current_message,
            max_tokens=max_tokens,
        )
        
        # Combine contexts
        context_parts = []
        
        if semantic_results:
            context_parts.append("[Relevant past conversations]")
            for i, result in enumerate(semantic_results, 1):
                text = result.get("text", "")
                context_parts.append(f"{i}. {text}")
            context_parts.append("")
            
        if compressed.get("context"):
            if compressed.get("summarized", 0) > 0:
                context_parts.append("[Recent conversation history (summarized)]")
            else:
                context_parts.append("[Recent conversation history]")
            context_parts.append(compressed["context"])
            
        return {
            "context": "\n".join(context_parts),
            "semantic_results": len(semantic_results),
            "history_turns": compressed.get("turns_included", 0),
            "summarized": compressed.get("summarized", 0),
            "estimated_tokens": compressed.get("estimated_tokens", 0),
        }
