"""
Memory Manager - coordinates vector store and conversation database
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages conversation memory using both vector store and SQL database
    """
    
    def __init__(self, vector_store, conversation_db):
        """
        Initialize memory manager
        
        Args:
            vector_store: VectorStore instance
            conversation_db: ConversationDB instance
        """
        self.vector_store = vector_store
        self.conversation_db = conversation_db
        logger.info("MemoryManager initialized")
    
    async def store_conversation(
        self,
        session_id: str,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        agent_mode: str,
        model_used: str,
        metadata: Dict[str, Any] = None
    ):
        """
        Store conversation in both vector store and SQL database
        """
        try:
            logger.info(f"Storing conversation {conversation_id} in session {session_id}")
            
            # Combine user and assistant messages for embedding
            combined_text = f"User: {user_message}\nAssistant: {assistant_message}"
            
            # Prepare metadata
            full_metadata = {
                'session_id': session_id,
                'agent_mode': agent_mode,
                'model_used': model_used,
                'timestamp': datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Store in vector database (for semantic search)
            await self.vector_store.add_conversation(
                conversation_id=conversation_id,
                text=combined_text,
                metadata=full_metadata
            )
            logger.info(f"Stored in vector store")
            
            # Store in SQL database (for structured queries)
            await self.conversation_db.store_conversation(
                conversation_id=conversation_id,
                session_id=session_id,
                user_message=user_message,
                assistant_message=assistant_message,
                agent_mode=agent_mode,
                model_used=model_used,
                metadata=full_metadata
            )
            logger.info(f"Stored in SQL database")
            
        except Exception as e:
            logger.error(f"Error storing conversation in memory: {e}")
            # Don't raise - memory storage failures shouldn't break the main flow
    
    async def retrieve_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_chunks: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from memory
        """
        try:
            logger.info(f"Retrieving context for query: '{query[:50]}...' session: {session_id}")
            
            # Build filter
            filter_metadata = {}
            if session_id:
                filter_metadata['session_id'] = session_id
            
            # Search vector store
            results = await self.vector_store.search_similar(
                query=query,
                max_results=max_chunks,
                filter_metadata=filter_metadata if filter_metadata else None
            )
            
            logger.info(f"Found {len(results)} results from vector search")
            
            # Log distances for debugging
            for i, r in enumerate(results):
                logger.info(f"Result {i}: distance={r.get('distance')}, text={r.get('text', '')[:50]}")
            
            # Filter by similarity threshold (lower distance = more similar)
            filtered_results = [
                r for r in results 
                if r.get('distance', 1.0) <= similarity_threshold
            ]
            
            logger.info(f"After filtering by threshold {similarity_threshold}: {len(filtered_results)} results")
            
            # If no results after filtering, increase threshold dynamically
            if not filtered_results and results:
                logger.warning(f"No results passed threshold {similarity_threshold}, using all results")
                filtered_results = results[:max_chunks]
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of conversations
            
        Returns:
            List of conversations
        """
        try:
            conversations = await self.conversation_db.get_session_conversations(
                session_id=session_id,
                limit=limit
            )
            return conversations
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return []
    
    async def delete_session(self, session_id: str):
        """
        Delete all conversations for a session (GDPR compliance)
        
        Args:
            session_id: Session identifier
        """
        # Implementation would delete from both stores
        # Left as TODO for production implementation
        pass
    
    async def search_conversations(
        self,
        query: str,
        agent_mode: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search across all conversations
        
        Args:
            query: Search query
            agent_mode: Optional agent mode filter
            limit: Maximum results
            
        Returns:
            List of matching conversations
        """
        try:
            filter_metadata = {}
            if agent_mode:
                filter_metadata['agent_mode'] = agent_mode
            
            results = await self.vector_store.search_similar(
                query=query,
                max_results=limit,
                filter_metadata=filter_metadata if filter_metadata else None
            )
            
            return results
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return []