"""
Design Agent - specialized for UI/UX design guidance.
"""

from typing import Optional

from src.agents.base_agent import BaseAgent


class DesignAgent(BaseAgent):
    """Agent specialized for design tasks"""

    def __init__(self, agent_mode: str = "design", model=None):
        super().__init__(agent_mode, model)
