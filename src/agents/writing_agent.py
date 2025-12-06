"""
Writing Agent - specialized for creative and professional writing
"""
from src.agents.base_agent import BaseAgent


class WritingAgent(BaseAgent):
    """Agent specialized for writing tasks"""

    def __init__(self, agent_mode: str = "writing", model=None):
        super().__init__(agent_mode, model)
