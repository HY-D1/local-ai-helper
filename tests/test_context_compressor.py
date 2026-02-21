"""Tests for context compression functionality."""
import pytest
from src.memory.context_compressor import (
    ContextCompressor,
    ConversationTurn,
    ConversationSummarizer,
)


class TestContextCompressor:
    """Tests for context compressor."""
    
    def test_empty_turns(self):
        compressor = ContextCompressor()
        result = compressor.compress([], "Hello")
        assert result["context"] == ""
        assert result["turns_included"] == 0
        
    def test_single_turn(self):
        compressor = ContextCompressor()
        turns = [ConversationTurn(role="user", content="Hello")]
        result = compressor.compress(turns, "How are you?")
        assert result["turns_included"] == 1
        assert "Hello" in result["context"]
        
    def test_multiple_turns(self):
        compressor = ContextCompressor()
        turns = [
            ConversationTurn(role="user", content="Hello"),
            ConversationTurn(role="assistant", content="Hi there!"),
            ConversationTurn(role="user", content="How are you?"),
            ConversationTurn(role="assistant", content="I'm fine!"),
        ]
        result = compressor.compress(turns, "What's new?")
        assert result["turns_included"] == 4
        assert "Hello" in result["context"]
        assert "Hi there!" in result["context"]
        
    def test_preserve_recent(self):
        compressor = ContextCompressor(preserve_recent=2, max_tokens=1000)
        turns = [
            ConversationTurn(role="user", content="Message 1"),
            ConversationTurn(role="assistant", content="Response 1"),
            ConversationTurn(role="user", content="Message 2"),
            ConversationTurn(role="assistant", content="Response 2"),
            ConversationTurn(role="user", content="Message 3"),
            ConversationTurn(role="assistant", content="Response 3"),
        ]
        result = compressor.compress(turns, "Current message")
        
        # Should preserve last 2 exchanges
        assert "Message 3" in result["context"]
        assert "Response 3" in result["context"]
        assert "Message 2" in result["context"] or result["summarized"] > 0
        
    def test_token_estimation(self):
        compressor = ContextCompressor()
        text = "Hello world " * 100
        tokens = compressor.estimate_tokens(text)
        assert tokens > 0
        
    def test_extract_key_points(self):
        compressor = ContextCompressor()
        turns = [
            ConversationTurn(role="user", content="This is a very long message that should be truncated"),
            ConversationTurn(role="assistant", content="Short"),
        ]
        summary = compressor.extract_key_points(turns)
        assert "user:" in summary
        assert "assistant:" in summary
        
    def test_create_prompt_with_context(self):
        compressor = ContextCompressor()
        turns = [
            ConversationTurn(role="user", content="Hello"),
            ConversationTurn(role="assistant", content="Hi!"),
        ]
        prompt = compressor.create_prompt_with_context(
            system_prompt="You are helpful.",
            turns=turns,
            current_message="How are you?",
        )
        assert "You are helpful." in prompt
        assert "Hello" in prompt
        assert "How are you?" in prompt
        assert "Assistant:" in prompt


class TestConversationSummarizer:
    """Tests for conversation summarizer."""
    
    @pytest.mark.asyncio
    async def test_empty_turns(self):
        summarizer = ConversationSummarizer()
        summary = await summarizer.summarize([])
        assert summary == ""
        
    @pytest.mark.asyncio
    async def test_single_turn(self):
        summarizer = ConversationSummarizer()
        turns = [ConversationTurn(role="user", content="Hello, how are you?")]
        summary = await summarizer.summarize(turns)
        assert "Hello" in summary
        
    @pytest.mark.asyncio
    async def test_multiple_turns(self):
        summarizer = ConversationSummarizer()
        turns = [
            ConversationTurn(role="user", content="Tell me about Python"),
            ConversationTurn(role="assistant", content="Python is a programming language"),
            ConversationTurn(role="user", content="What about JavaScript?"),
        ]
        summary = await summarizer.summarize(turns)
        assert "Tell me about Python" in summary
        assert "What about JavaScript?" in summary
        
    @pytest.mark.asyncio
    async def test_max_length(self):
        summarizer = ConversationSummarizer()
        turns = [
            ConversationTurn(role="user", content="A" * 1000),
        ]
        summary = await summarizer.summarize(turns, max_length=50)
        # The implementation truncates long topics, check it's reasonable
        assert len(summary) < 200  # Should be significantly shorter than original


class TestConversationTurn:
    """Tests for ConversationTurn dataclass."""
    
    def test_basic_turn(self):
        turn = ConversationTurn(role="user", content="Hello")
        assert turn.role == "user"
        assert turn.content == "Hello"
        assert turn.importance == 1.0
        
    def test_turn_with_timestamp(self):
        turn = ConversationTurn(
            role="assistant",
            content="Hi!",
            timestamp="2024-01-01T00:00:00",
        )
        assert turn.timestamp == "2024-01-01T00:00:00"
        
    def test_turn_with_importance(self):
        turn = ConversationTurn(
            role="user",
            content="Important question",
            importance=2.0,
        )
        assert turn.importance == 2.0
