"""
Math Agent - specialized for mathematical problem solving.
"""
import re
from typing import Optional

from src.agents.base_agent import BaseAgent


class MathAgent(BaseAgent):
    """Agent specialized for math problems with calculator tool."""

    def __init__(
        self, agent_mode: str = "math", model: Optional[str] = None, *, validate_model: Optional[bool] = None
    ) -> None:
        super().__init__(agent_mode, model, validate_model=validate_model, enable_tools=True)

    async def preprocess(self, message: str) -> str:
        """Format math expressions for better parsing."""
        # Check if message contains LaTeX or already formatted expressions
        if "\\" in message or "$" in message:
            return message

        # Replace ^ with ** for exponentiation if not in a code block
        lines = message.split("\n")
        processed_lines = []
        in_code_block = False
        
        for line in lines:
            if "```" in line:
                in_code_block = not in_code_block
            
            if not in_code_block:
                # Replace ^ with ** for exponentiation
                line = re.sub(r'(\d+)\^(\d+)', r'\1**\2', line)
                
            processed_lines.append(line)
            
        return "\n".join(processed_lines)

    async def postprocess(self, response: str) -> str:
        """Format math output with proper LaTeX."""
        # Ensure code blocks with math are properly formatted
        response = self._format_equations(response)
        return response
        
    def _format_equations(self, text: str) -> str:
        """Convert plain text equations to formatted versions."""
        # Wrap standalone math expressions in code blocks
        lines = text.split("\n")
        result = []
        
        for line in lines:
            # Detect potential equation lines (simple heuristic)
            stripped = line.strip()
            if ("=" in stripped and 
                not stripped.startswith("$") and 
                any(c in stripped for c in "+-*/^()0123456789")):
                # Check if it's a calculation result line
                if re.match(r'^[\d\s\+\-\*/\^\(\)\.=]+$', stripped):
                    line = f"`{stripped}`"
                    
            result.append(line)
            
        return "\n".join(result)
