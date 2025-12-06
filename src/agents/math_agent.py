"""
Math Agent - specialized for mathematical problem solving.
"""

from typing import Optional

from src.agents.base_agent import BaseAgent


class MathAgent(BaseAgent):
    """Agent specialized for math problems."""

    def __init__(
        self, agent_mode: str = "math", model: Optional[str] = None, *, validate_model: Optional[bool] = None
    ) -> None:
        super().__init__(agent_mode, model, validate_model=validate_model)

    async def preprocess(self, message: str) -> str:
        """Format math expressions for better parsing."""
        if "\\" in message or "$" in message:
            return message

        return message.replace("^", "**")

    async def postprocess(self, response: str) -> str:
        """Format math output with proper LaTeX."""
        return response
