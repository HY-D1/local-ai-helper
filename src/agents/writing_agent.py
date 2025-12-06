"""
Writing Agent - specialized for creative and professional writing.
"""

from typing import Optional

from src.agents.base_agent import BaseAgent


class WritingAgent(BaseAgent):
    """Agent specialized for writing tasks."""

    def __init__(
        self, agent_mode: str = "writing", model: Optional[str] = None, *, validate_model: Optional[bool] = None
    ) -> None:
        super().__init__(agent_mode, model, validate_model=validate_model)
