"""
Code Agent - specialized for programming tasks
"""
import re
from src.agents.base_agent import BaseAgent


class CodeAgent(BaseAgent):
    """Agent specialized for code-related tasks"""
    
    def __init__(self, agent_mode: str = 'code', model=None):
        super().__init__(agent_mode, model)
    
    async def preprocess(self, message: str) -> str:
        """Format code context"""
        # Detect code blocks and preserve formatting
        return message
    
    async def postprocess(self, response: str) -> str:
        """Ensure code is properly formatted"""
        # Add language hints to code blocks if missing
        if '```' in response and not re.search(r'```\w+', response):
            response = response.replace('```\n', '```python\n', 1)
        return response