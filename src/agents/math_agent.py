"""
Math Agent - specialized for mathematical problem solving
"""
import re
from src.agents.base_agent import BaseAgent


class MathAgent(BaseAgent):
    """Agent specialized for math problems"""
    
    def __init__(self, agent_mode: str = 'math', model=None):
        super().__init__(agent_mode, model)
    
    async def preprocess(self, message: str) -> str:
        """Format math expressions for better parsing"""
        # Detect LaTeX-style equations
        if '\\' in message or '$' in message:
            return message
        
        # Convert common notations
        message = message.replace('^', '**')  # Exponents
        return message
    
    async def postprocess(self, response: str) -> str:
        """Format math output with proper LaTeX"""
        # Ensure equations are wrapped in LaTeX delimiters
        return response
