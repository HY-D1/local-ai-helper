"""
Tool system for agents - enables agents to use external tools.
"""
import json
import logging
import math
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    description: str
    type: str = "string"
    required: bool = True
    enum: Optional[List[str]] = None
    default: Any = None


@dataclass
class ToolDefinition:
    """Definition of a tool that can be used by agents."""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for LLM prompting."""
        params = {}
        required = []
        
        for param in self.parameters:
            param_def = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                param_def["enum"] = param.enum
            params[param.name] = param_def
            
            if param.required:
                required.append(param.name)
                
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": params,
                "required": required,
            },
        }


class BaseTool(ABC):
    """Base class for all tools."""
    
    def __init__(self, definition: ToolDefinition):
        self.definition = definition
        
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass
        
    def get_definition(self) -> Dict[str, Any]:
        """Get tool definition for LLM."""
        return self.definition.to_dict()


class CalculatorTool(BaseTool):
    """Calculator tool for mathematical expressions."""
    
    def __init__(self):
        super().__init__(
            ToolDefinition(
                name="calculator",
                description="Evaluate mathematical expressions safely",
                parameters=[
                    ToolParameter(
                        name="expression",
                        description="Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', '10!')",
                        type="string",
                        required=True,
                    ),
                ],
            )
        )
        
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Safely evaluate a mathematical expression."""
        expression = kwargs.get("expression", "")
        
        if not expression:
            return {"error": "No expression provided"}
            
        try:
            # Whitelist of allowed functions and constants
            safe_dict = {
                "sqrt": math.sqrt,
                "pow": math.pow,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "abs": abs,
                "round": round,
                "max": max,
                "min": min,
                "sum": sum,
                "pi": math.pi,
                "e": math.e,
                "factorial": math.factorial,
            }
            
            # Replace ^ with ** for exponentiation
            expression = expression.replace("^", "**")
            
            # Evaluate with limited globals
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            return {
                "result": result,
                "expression": expression,
            }
        except Exception as e:
            return {
                "error": f"Failed to evaluate expression: {str(e)}",
                "expression": expression,
            }


class UnitConverterTool(BaseTool):
    """Unit conversion tool."""
    
    CONVERSIONS = {
        # Length
        "m_to_ft": 3.28084,
        "ft_to_m": 0.3048,
        "km_to_mi": 0.621371,
        "mi_to_km": 1.60934,
        "cm_to_in": 0.393701,
        "in_to_cm": 2.54,
        # Weight
        "kg_to_lb": 2.20462,
        "lb_to_kg": 0.453592,
        "g_to_oz": 0.035274,
        "oz_to_g": 28.3495,
        # Temperature (special handling)
        "c_to_f": lambda c: (c * 9/5) + 32,
        "f_to_c": lambda f: (f - 32) * 5/9,
        # Volume
        "l_to_gal": 0.264172,
        "gal_to_l": 3.78541,
        "ml_to_floz": 0.033814,
        "floz_to_ml": 29.5735,
    }
    
    def __init__(self):
        super().__init__(
            ToolDefinition(
                name="unit_converter",
                description="Convert between different units of measurement",
                parameters=[
                    ToolParameter(
                        name="value",
                        description="Numeric value to convert",
                        type="number",
                        required=True,
                    ),
                    ToolParameter(
                        name="from_unit",
                        description="Source unit (e.g., 'm', 'kg', 'c', 'l')",
                        type="string",
                        required=True,
                    ),
                    ToolParameter(
                        name="to_unit",
                        description="Target unit (e.g., 'ft', 'lb', 'f', 'gal')",
                        type="string",
                        required=True,
                    ),
                ],
            )
        )
        
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Convert between units."""
        value = kwargs.get("value")
        from_unit = kwargs.get("from_unit", "").lower()
        to_unit = kwargs.get("to_unit", "").lower()
        
        if value is None:
            return {"error": "No value provided"}
            
        key = f"{from_unit}_to_{to_unit}"
        
        if key in self.CONVERSIONS:
            conversion = self.CONVERSIONS[key]
            if callable(conversion):
                result = conversion(value)
            else:
                result = value * conversion
                
            return {
                "result": round(result, 4),
                "from": f"{value} {from_unit}",
                "to": f"{result:.4f} {to_unit}",
            }
        else:
            return {
                "error": f"Conversion from '{from_unit}' to '{to_unit}' not supported",
                "supported": list(self.CONVERSIONS.keys()),
            }


class CodeExecutorTool(BaseTool):
    """Tool for executing simple Python code snippets."""
    
    def __init__(self):
        super().__init__(
            ToolDefinition(
                name="code_executor",
                description="Execute Python code and return the output (read-only, no file/system access)",
                parameters=[
                    ToolParameter(
                        name="code",
                        description="Python code to execute",
                        type="string",
                        required=True,
                    ),
                ],
            )
        )
        
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute Python code in a restricted environment."""
        code = kwargs.get("code", "")
        
        if not code:
            return {"error": "No code provided"}
            
        try:
            # Create restricted globals
            safe_builtins = {
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "pow": pow,
                "divmod": divmod,
                "sorted": sorted,
                "reversed": reversed,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "print": lambda *args: " ".join(str(a) for a in args),
            }
            
            restricted_globals = {
                "__builtins__": safe_builtins,
            }
            
            # Execute code
            exec_globals = restricted_globals.copy()
            exec(code, exec_globals)
            
            # Get result (check for common variable names)
            result_keys = ["result", "output", "answer", "_"]
            result = None
            for key in result_keys:
                if key in exec_globals:
                    result = exec_globals[key]
                    break
                    
            return {
                "result": result,
                "executed": True,
            }
        except Exception as e:
            return {
                "error": str(e),
                "executed": False,
            }


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.register_default_tools()
        
    def register_default_tools(self):
        """Register default built-in tools."""
        self.register(CalculatorTool())
        self.register(UnitConverterTool())
        self.register(CodeExecutorTool())
        
    def register(self, tool: BaseTool):
        """Register a tool."""
        self.tools[tool.definition.name] = tool
        logger.info(f"Registered tool: {tool.definition.name}")
        
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(name)
        
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())
        
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get definitions for all tools."""
        return [tool.get_definition() for tool in self.tools.values()]
        
    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            return {"error": f"Tool '{name}' not found"}
            
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return {"error": f"Tool execution failed: {str(e)}"}


class ToolParser:
    """Parse tool calls from LLM responses."""
    
    # Pattern to match tool calls: @tool_name(param1="value1", param2="value2")
    TOOL_PATTERN = r'@(\w+)\((.*?)\)(?![^()]*\))'
    
    @classmethod
    def parse_tool_calls(cls, text: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from text.
        
        Args:
            text: Text potentially containing tool calls
            
        Returns:
            List of parsed tool calls with name and parameters
        """
        calls = []
        
        for match in re.finditer(cls.TOOL_PATTERN, text, re.DOTALL):
            tool_name = match.group(1)
            params_str = match.group(2)
            
            # Parse parameters
            params = {}
            try:
                # Try to parse as JSON-like object
                params_json = "{" + params_str + "}"
                params = json.loads(params_json)
            except json.JSONDecodeError:
                # Manual parsing for simple key=value pairs
                param_pattern = r'(\w+)=[\'"]([^\'"]*)[\'"]'
                for pm in re.finditer(param_pattern, params_str):
                    params[pm.group(1)] = pm.group(2)
                    
            calls.append({
                "name": tool_name,
                "parameters": params,
                "raw": match.group(0),
            })
            
        return calls
        
    @classmethod
    def replace_tool_calls(cls, text: str, replacements: Dict[str, str]) -> str:
        """
        Replace tool calls with their results.
        
        Args:
            text: Original text
            replacements: Mapping of raw tool call strings to replacement strings
            
        Returns:
            Text with tool calls replaced
        """
        result = text
        for raw, replacement in replacements.items():
            result = result.replace(raw, replacement)
        return result


def format_tools_prompt(tools: List[Dict[str, Any]]) -> str:
    """
    Format tool definitions for inclusion in system prompt.
    
    Args:
        tools: List of tool definitions
        
    Returns:
        Formatted prompt section
    """
    if not tools:
        return ""
        
    lines = ["\n[Available Tools]"]
    lines.append("You have access to the following tools:")
    
    for tool in tools:
        lines.append(f"\n{tool['name']}:")
        lines.append(f"  Description: {tool['description']}")
        lines.append("  Parameters:")
        
        params = tool.get("parameters", {}).get("properties", {})
        required = tool.get("parameters", {}).get("required", [])
        
        for param_name, param_def in params.items():
            req_marker = " (required)" if param_name in required else ""
            lines.append(f"    - {param_name}: {param_def.get('description', '')}{req_marker}")
            
    lines.append("\nTo use a tool, include it in your response like:")
    lines.append('  @tool_name(parameter="value")')
    lines.append("\nThe tool result will be provided for you to incorporate into your response.")
    
    return "\n".join(lines)
