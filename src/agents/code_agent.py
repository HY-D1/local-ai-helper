"""
Code Agent - specialized for programming tasks.
"""

import re
from typing import Optional

from src.agents.base_agent import BaseAgent


class CodeAgent(BaseAgent):
    """Agent specialized for code-related tasks."""

    def __init__(
        self, agent_mode: str = "code", model: Optional[str] = None, *, validate_model: Optional[bool] = None
    ) -> None:
        super().__init__(agent_mode, model, validate_model=validate_model)

    async def preprocess(self, message: str) -> str:
        """Format code context."""
        return message

    async def postprocess(self, response: str) -> str:
        """Ensure code is properly formatted."""
        if "```" in response and not re.search(r"```\w+", response):
            response = response.replace("```\n", "```python\n", 1)
        return response
