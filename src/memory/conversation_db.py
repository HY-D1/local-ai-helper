"""
Conversation Database using PostgreSQL.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg

logger = logging.getLogger(__name__)


class ConversationDB:
    """Manages conversation persistence in PostgreSQL."""

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL")
        self.pool: Optional[asyncpg.pool.Pool] = None

    async def initialize(self) -> None:
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
            )
            logger.info("Database pool initialized")
        except Exception as exc:  # noqa: BLE001
            logger.error("Database initialization failed: %s", exc)
            raise

    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

    async def store_conversation(
        self,
        conversation_id: str,
        session_id: str,
        user_message: str,
        assistant_message: str,
        agent_mode: str,
        model_used: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a conversation in the database."""
        try:
            import json

            if not self.pool:
                raise RuntimeError("Database pool is not initialized")

            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO conversations
                    (id, session_id, user_message, assistant_message, agent_mode, model_used, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    UUID(conversation_id),
                    session_id,
                    user_message,
                    assistant_message,
                    agent_mode,
                    model_used,
                    json.dumps(metadata or {}),
                )
            logger.debug("Stored conversation %s", conversation_id)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error storing conversation: %s", exc)
            raise

    async def get_session_conversations(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get all conversations for a session."""
        try:
            if not self.pool:
                raise RuntimeError("Database pool is not initialized")

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, user_message, assistant_message, agent_mode,
                           model_used, created_at, metadata
                    FROM conversations
                    WHERE session_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    session_id,
                    limit,
                )

                return [
                    {
                        "id": str(row["id"]),
                        "user_message": row["user_message"],
                        "assistant_message": row["assistant_message"],
                        "agent_mode": row["agent_mode"],
                        "model_used": row["model_used"],
                        "created_at": row["created_at"].isoformat(),
                        "metadata": row["metadata"],
                    }
                    for row in rows
                ]
        except Exception as exc:  # noqa: BLE001
            logger.error("Error retrieving conversations: %s", exc)
            return []

    async def health_check(self) -> bool:
        """Check database health."""
        try:
            if not self.pool:
                return False
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:  # noqa: BLE001
            return False
