"""
Memory Manager - coordinates vector store and conversation database.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "agent_configs.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)


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
        self.similarity_threshold = CONFIG.get("memory", {}).get("similarity_threshold", 0.3)
        self.max_chunks = CONFIG.get("memory", {}).get("max_retrieved_chunks", 5)
        logger.info("MemoryManager initialized")

    async def store_conversation(
        self,
        session_id: str,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        agent_mode: str,
        model_used: str,
        metadata: Dict[str, Any] = None,
    ):
        """Store conversation in both vector store and SQL database."""
        try:
            logger.info(f"Storing conversation {conversation_id} in session {session_id}")

            combined_text = f"User: {user_message}\nAssistant: {assistant_message}"

            full_metadata = {
                "session_id": session_id,
                "agent_mode": agent_mode,
                "model_used": model_used,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {}),
            }

            await self.vector_store.add_conversation(
                conversation_id=conversation_id,
                text=combined_text,
                metadata=full_metadata,
            )
            logger.info("Stored in vector store")

            await self.conversation_db.store_conversation(
                conversation_id=conversation_id,
                session_id=session_id,
                user_message=user_message,
                assistant_message=assistant_message,
                agent_mode=agent_mode,
                model_used=model_used,
                metadata=full_metadata,
            )
            logger.info("Stored in SQL database")

        except Exception as e:
            logger.error(f"Error storing conversation in memory: {e}")

    async def retrieve_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_chunks: int = 5,
        similarity_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context from memory."""
        try:
            logger.info("Retrieving context for query: '%s...' session: %s", query[:50], session_id)

            filter_metadata = {}
            if session_id:
                filter_metadata["session_id"] = session_id

            results = await self.vector_store.search_similar(
                query=query,
                max_results=max_chunks,
                filter_metadata=filter_metadata if filter_metadata else None,
            )

            logger.info("Found %d results from vector search", len(results))
            for i, r in enumerate(results):
                logger.info("Result %d: distance=%s, text=%s", i, r.get("distance"), r.get("text", "")[:50])

            filtered_results = [
                r for r in results if r.get("distance", 1.0) <= similarity_threshold
            ]

            logger.info("After filtering by threshold %s: %d results", similarity_threshold, len(filtered_results))

            if not filtered_results and results:
                logger.warning("No results passed threshold %s, using all results", similarity_threshold)
                filtered_results = results[:max_chunks]

            return filtered_results

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []

    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        try:
            conversations = await self.conversation_db.get_session_conversations(
                session_id=session_id,
                limit=limit,
            )
            return conversations
        except Exception as exc:  # noqa: BLE001
            logger.error("Error getting session history: %s", exc)
            return []

    async def delete_session(self, session_id: str):
        """Delete all conversations for a session across storage layers."""
        try:
            vector_deleted = False
            if hasattr(self.vector_store, "delete_by_session"):
                vector_deleted = await self.vector_store.delete_by_session(session_id)

            deleted_rows = await self.conversation_db.delete_session(session_id)

            return {
                "vectors_removed": vector_deleted,
                "deleted_rows": deleted_rows,
            }
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            raise

    async def search_conversations(
        self,
        query: str,
        agent_mode: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search across all conversations."""
        try:
            filter_metadata = {}
            if agent_mode:
                filter_metadata["agent_mode"] = agent_mode

            results = await self.vector_store.search_similar(
                query=query,
                max_results=limit,
                filter_metadata=filter_metadata if filter_metadata else None,
            )

            return results
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return []
