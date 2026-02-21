"""
Context compression for long conversations.
Implements sliding window with summarization for long-term memory.
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single conversation turn."""
    role: str
    content: str
    timestamp: Optional[str] = None
    importance: float = 1.0  # For future importance scoring


class ContextCompressor:
    """
    Compresses conversation history to fit within token limits.
    Uses a sliding window with optional summarization.
    """
    
    def __init__(
        self,
        max_tokens: int = 4096,
        tokens_per_message: int = 4,
        tokens_per_character: float = 0.25,
        preserve_recent: int = 4,
    ):
        self.max_tokens = max_tokens
        self.tokens_per_message = tokens_per_message
        self.tokens_per_character = tokens_per_character
        self.preserve_recent = preserve_recent
        
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        return int(len(text) * self.tokens_per_character) + self.tokens_per_message
        
    def extract_key_points(self, turns: List[ConversationTurn]) -> str:
        """
        Extract key points from conversation turns.
        Simple extraction - can be enhanced with LLM-based summarization.
        """
        if not turns:
            return ""
            
        key_points = []
        for turn in turns:
            content = turn.content.strip()
            if len(content) > 100:
                # Truncate long messages
                content = content[:100] + "..."
            key_points.append(f"{turn.role}: {content}")
            
        return " | ".join(key_points)
        
    def compress(
        self,
        turns: List[ConversationTurn],
        current_message: str = "",
    ) -> Dict[str, Any]:
        """
        Compress conversation history to fit within token budget.
        
        Strategy:
        1. Always keep the most recent N turns in full
        2. Summarize older turns if needed
        3. If still over budget, progressively remove oldest summaries
        
        Args:
            turns: List of conversation turns
            current_message: The current user message (to reserve space for)
            
        Returns:
            Dict with compressed context and metadata
        """
        if not turns:
            return {"context": "", "turns_included": 0, "summarized": 0}
            
        # Reserve tokens for current message and response
        reserved_tokens = self.estimate_tokens(current_message) + 500
        available_tokens = self.max_tokens - reserved_tokens
        
        # Split into recent (preserve) and older (potentially summarize)
        recent_turns = turns[-self.preserve_recent:] if len(turns) > self.preserve_recent else turns
        older_turns = turns[:-self.preserve_recent] if len(turns) > self.preserve_recent else []
        
        # Calculate tokens for recent turns
        recent_tokens = sum(self.estimate_tokens(t.content) for t in recent_turns)
        
        context_parts = []
        summarized_count = 0
        
        # If we have older turns and room for a summary
        if older_turns and available_tokens > recent_tokens + 100:
            summary = self.extract_key_points(older_turns)
            summary_tokens = self.estimate_tokens(summary)
            
            # Check if summary + recent fits
            if summary_tokens + recent_tokens <= available_tokens:
                context_parts.append(f"[Previous conversation summary: {summary}]")
                summarized_count = len(older_turns)
            else:
                # Just include a subset of recent older turns
                tokens_used = 0
                included_older = []
                for turn in reversed(older_turns):
                    turn_tokens = self.estimate_tokens(turn.content)
                    if tokens_used + turn_tokens + recent_tokens <= available_tokens:
                        included_older.insert(0, turn)
                        tokens_used += turn_tokens
                    else:
                        break
                
                if included_older:
                    context_parts.extend([f"{t.role}: {t.content}" for t in included_older])
                    
        # Add recent turns
        context_parts.extend([f"{t.role}: {t.content}" for t in recent_turns])
        
        context = "\n".join(context_parts)
        
        # Final token check
        total_tokens = self.estimate_tokens(context)
        
        return {
            "context": context,
            "turns_included": len(recent_turns) + (summarized_count if summarized_count > 0 else 0),
            "summarized": summarized_count,
            "estimated_tokens": total_tokens,
            "available_tokens": available_tokens,
        }
        
    def create_prompt_with_context(
        self,
        system_prompt: str,
        turns: List[ConversationTurn],
        current_message: str,
    ) -> str:
        """
        Create a complete prompt with compressed context.
        
        Args:
            system_prompt: The system instruction
            turns: Conversation history
            current_message: Current user message
            
        Returns:
            Complete prompt string
        """
        compression_result = self.compress(turns, current_message)
        
        parts = [system_prompt]
        
        if compression_result["context"]:
            parts.append("\n[Conversation Context]")
            parts.append(compression_result["context"])
            
        parts.append(f"\nUser: {current_message}")
        parts.append("Assistant:")
        
        return "\n".join(parts)


class ConversationSummarizer:
    """
    Summarizes conversation history using an LLM.
    This is a placeholder for LLM-based summarization.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name
        
    async def summarize(
        self,
        turns: List[ConversationTurn],
        max_length: int = 200,
    ) -> str:
        """
        Summarize conversation turns.
        
        In production, this would call an LLM to generate a summary.
        For now, returns a simple concatenation of key points.
        """
        if not turns:
            return ""
            
        # Simple extraction-based summary
        topics = []
        for turn in turns:
            if turn.role == "user":
                # Extract first sentence or first 50 chars
                content = turn.content.strip()
                preview = content.split(".")[0][:50]
                if preview:
                    topics.append(preview)
                    
        summary = " | ".join(topics[:5])  # Top 5 topics
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
            
        return f"Topics discussed: {summary}"
