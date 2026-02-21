"""Tests for the tools system."""
import pytest
from src.agents.tools import (
    ToolRegistry,
    ToolDefinition,
    ToolParameter,
    CalculatorTool,
    UnitConverterTool,
    CodeExecutorTool,
    ToolParser,
    format_tools_prompt,
)


class TestCalculatorTool:
    """Tests for calculator tool."""
    
    @pytest.mark.asyncio
    async def test_basic_addition(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="2 + 2")
        assert result["result"] == 4
        
    @pytest.mark.asyncio
    async def test_power(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="2 ** 8")
        assert result["result"] == 256
        
    @pytest.mark.asyncio
    async def test_sqrt(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="sqrt(16)")
        assert result["result"] == 4.0
        
    @pytest.mark.asyncio
    async def test_factorial(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="factorial(5)")
        assert result["result"] == 120
        
    @pytest.mark.asyncio
    async def test_invalid_expression(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="invalid")
        assert "error" in result
        
    @pytest.mark.asyncio
    async def test_empty_expression(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="")
        assert "error" in result
        
    def test_definition(self):
        tool = CalculatorTool()
        definition = tool.get_definition()
        assert definition["name"] == "calculator"
        assert "expression" in definition["parameters"]["properties"]


class TestUnitConverterTool:
    """Tests for unit converter tool."""
    
    @pytest.mark.asyncio
    async def test_meters_to_feet(self):
        tool = UnitConverterTool()
        result = await tool.execute(value=1, from_unit="m", to_unit="ft")
        assert "result" in result
        assert result["result"] > 3.2
        
    @pytest.mark.asyncio
    async def test_celsius_to_fahrenheit(self):
        tool = UnitConverterTool()
        result = await tool.execute(value=0, from_unit="c", to_unit="f")
        assert result["result"] == 32.0
        
    @pytest.mark.asyncio
    async def test_kg_to_lb(self):
        tool = UnitConverterTool()
        result = await tool.execute(value=1, from_unit="kg", to_unit="lb")
        assert result["result"] > 2.0
        
    @pytest.mark.asyncio
    async def test_unsupported_conversion(self):
        tool = UnitConverterTool()
        result = await tool.execute(value=1, from_unit="xyz", to_unit="abc")
        assert "error" in result
        
    @pytest.mark.asyncio
    async def test_no_value(self):
        tool = UnitConverterTool()
        result = await tool.execute(from_unit="m", to_unit="ft")
        assert "error" in result


class TestCodeExecutorTool:
    """Tests for code executor tool."""
    
    @pytest.mark.asyncio
    async def test_simple_calculation(self):
        tool = CodeExecutorTool()
        result = await tool.execute(code="result = 2 + 2")
        assert result["executed"] is True
        assert result["result"] == 4
        
    @pytest.mark.asyncio
    async def test_list_operations(self):
        tool = CodeExecutorTool()
        result = await tool.execute(code="result = sum([1, 2, 3, 4, 5])")
        assert result["result"] == 15
        
    @pytest.mark.asyncio
    async def test_no_code(self):
        tool = CodeExecutorTool()
        result = await tool.execute(code="")
        assert "error" in result
        
    @pytest.mark.asyncio
    async def test_syntax_error(self):
        tool = CodeExecutorTool()
        result = await tool.execute(code="invalid syntax here!!!")
        assert result["executed"] is False
        assert "error" in result


class TestToolRegistry:
    """Tests for tool registry."""
    
    def test_default_tools(self):
        registry = ToolRegistry()
        tools = registry.list_tools()
        assert "calculator" in tools
        assert "unit_converter" in tools
        assert "code_executor" in tools
        
    def test_get_tool(self):
        registry = ToolRegistry()
        tool = registry.get_tool("calculator")
        assert tool is not None
        assert tool.definition.name == "calculator"
        
    def test_get_nonexistent_tool(self):
        registry = ToolRegistry()
        tool = registry.get_tool("nonexistent")
        assert tool is None
        
    @pytest.mark.asyncio
    async def test_execute_tool(self):
        registry = ToolRegistry()
        result = await registry.execute_tool("calculator", expression="5 * 5")
        assert result["result"] == 25
        
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        registry = ToolRegistry()
        result = await registry.execute_tool("nonexistent", param="value")
        assert "error" in result


class TestToolParser:
    """Tests for tool parser."""
    
    def test_parse_simple_tool_call(self):
        text = '@calculator(expression="2 + 2")'
        calls = ToolParser.parse_tool_calls(text)
        assert len(calls) == 1
        assert calls[0]["name"] == "calculator"
        assert calls[0]["parameters"]["expression"] == "2 + 2"
        
    def test_parse_multiple_tool_calls(self):
        text = '@calculator(expression="1 + 1") and @unit_converter(value=10, from_unit="m", to_unit="ft")'
        calls = ToolParser.parse_tool_calls(text)
        assert len(calls) == 2
        
    def test_parse_no_tool_calls(self):
        text = "This is just a normal response"
        calls = ToolParser.parse_tool_calls(text)
        assert len(calls) == 0
        
    def test_replace_tool_calls(self):
        text = '@calculator(expression="2 + 2")'
        replacements = {'@calculator(expression="2 + 2")': "The result is 4"}
        result = ToolParser.replace_tool_calls(text, replacements)
        assert result == "The result is 4"


class TestFormatToolsPrompt:
    """Tests for formatting tools prompt."""
    
    def test_format_empty_tools(self):
        result = format_tools_prompt([])
        assert result == ""
        
    def test_format_tools(self):
        tools = [
            {
                "name": "calculator",
                "description": "Do math",
                "parameters": {
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Math expression",
                        }
                    },
                    "required": ["expression"],
                },
            }
        ]
        result = format_tools_prompt(tools)
        assert "calculator" in result
        assert "expression" in result
        assert "required" in result
