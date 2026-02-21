"""
Base Agent class for all specialized agents.
"""
import asyncio
import logging
import os
import re
from abc import ABC
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional, Tuple, List

import ollama
import yaml

from src.agents.model_selector import select_model
from src.agents.tools import ToolRegistry, ToolParser, format_tools_prompt

logger = logging.getLogger(__name__)

# Load config once at import
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "agent_configs.yaml"
with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents
    """

    _validated_models = set()

    def __init__(
        self, 
        agent_mode: str, 
        model: Optional[str] = None, 
        *, 
        validate_model: Optional[bool] = None,
        enable_tools: bool = True,
    ):
        """
        Initialize the agent

        Args:
            agent_mode: Agent mode (general, math, code, writing, design).
            model: Model to use (defaults to configured model).
            validate_model: Whether to validate the model is installed. Defaults to
                the ``SKIP_MODEL_VALIDATION`` environment variable (False disables
                validation).
            enable_tools: Whether to enable tool usage for this agent.
        """
        self.agent_mode = agent_mode
        self.config = CONFIG["agents"].get(agent_mode, CONFIG["agents"]["general"])
        self.model = select_model(
            model or CONFIG["models"]["default"],
            CONFIG["models"],
        )
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        # Validate model exists once per model name to avoid repeated API calls
        env_skip_validation = bool(os.getenv("SKIP_MODEL_VALIDATION"))
        self.validate_model = validate_model if validate_model is not None else not env_skip_validation

        if self.validate_model and self.model not in self._validated_models:
            try:
                ollama.show(self.model)
                self._validated_models.add(self.model)
            except Exception as e:
                logger.warning(f"Model {self.model} not found: {e}")
                raise ValueError(
                    f"Model '{self.model}' not installed. Please download it first."
                )

        # Initialize tool registry
        self.enable_tools = enable_tools and self.config.get("tools", [])
        self.tool_registry = ToolRegistry() if self.enable_tools else None
        
        # Track conversation turns for context compression
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = CONFIG.get("memory", {}).get("max_context_messages", 10)

        logger.info(f"Initialized {agent_mode} agent with model {self.model}")

    def _build_prompt(
        self, 
        message: str, 
        context: str = "",
        include_tools: bool = True,
    ) -> str:
        """
        Build the complete prompt with system message and context

        Args:
            message: User message
            context: Retrieved context from memory
            include_tools: Whether to include tool definitions

        Returns:
            Complete prompt string
        """
        system_prompt = self.config["system_prompt"]
        
        # Add tool definitions if enabled
        if include_tools and self.tool_registry:
            tools = self.tool_registry.get_tool_definitions()
            if tools:
                system_prompt += format_tools_prompt(tools)

        if context:
            prompt = f"{system_prompt}\n\nRelevant Context:\n{context}\n\nUser: {message}"
        else:
            prompt = f"{system_prompt}\n\nUser: {message}"

        return prompt

    async def _process_tool_calls(self, response: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process any tool calls in the response.
        
        Args:
            response: Raw response from model
            
        Returns:
            Tuple of (processed response, list of tool results)
        """
        if not self.tool_registry:
            return response, []
            
        tool_calls = ToolParser.parse_tool_calls(response)
        if not tool_calls:
            return response, []
            
        tool_results = []
        replacements = {}
        
        for call in tool_calls:
            tool_name = call["name"]
            params = call["parameters"]
            
            logger.info(f"Executing tool: {tool_name} with params: {params}")
            
            result = await self.tool_registry.execute_tool(tool_name, **params)
            tool_results.append({
                "tool": tool_name,
                "params": params,
                "result": result,
            })
            
            # Format result for replacement
            if "error" in result:
                replacement = f"[Tool '{tool_name}' error: {result['error']}]"
            else:
                result_str = str(result.get("result", result))
                replacement = f"[Tool '{tool_name}' result: {result_str}]"
                
            replacements[call["raw"]] = replacement
            
        # Replace tool calls with results
        processed = ToolParser.replace_tool_calls(response, replacements)
        
        return processed, tool_results

    async def generate(
        self,
        message: str,
        context: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate a response

        Args:
            message: User message
            context: Retrieved context from memory
            temperature: Override config temperature
            max_tokens: Override config max_tokens
            **kwargs: Additional generation parameters

        Returns:
            Dict with response and metadata
        """
        try:
            # Preprocess message (can be overridden by subclasses)
            processed_message = await self.preprocess(message)

            # Build prompt
            prompt = self._build_prompt(processed_message, context)

            # Use provided params or fall back to config
            gen_temp = temperature if temperature is not None else self.config.get("temperature", 0.7)
            gen_tokens = max_tokens if max_tokens is not None else self.config.get("max_tokens", 2048)

            # Generate response without blocking the event loop
            response = await asyncio.to_thread(
                ollama.generate,
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": gen_temp,
                    "top_p": self.config.get("top_p", 0.9),
                    "num_predict": gen_tokens,
                },
            )

            raw_response = response["response"]
            
            # Process tool calls if any
            processed_response, tool_results = await self._process_tool_calls(raw_response)
            
            # If tools were called, generate a follow-up response with tool results
            if tool_results and not processed_response.strip():
                tool_context = "\n".join([
                    f"Tool '{tr['tool']}' result: {tr['result']}"
                    for tr in tool_results
                ])
                prompt_with_results = self._build_prompt(
                    f"{processed_message}\n\nTool results:\n{tool_context}",
                    context,
                    include_tools=False,
                )
                
                response = await asyncio.to_thread(
                    ollama.generate,
                    model=self.model,
                    prompt=prompt_with_results,
                    options={
                        "temperature": gen_temp,
                        "top_p": self.config.get("top_p", 0.9),
                        "num_predict": gen_tokens,
                    },
                )
                processed_response = response["response"]

            # Postprocess response (can be overridden by subclasses)
            final_response = await self.postprocess(processed_response)
            
            # Update conversation history
            self._update_history(message, final_response)

            return {
                "response": final_response,
                "model_used": self.model,
                "agent_mode": self.agent_mode,
                "tokens": response.get("tokens", 0),
                "tool_calls": len(tool_results),
            }

        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise

    async def generate_stream(
        self,
        message: str,
        context: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a streaming response

        Args:
            message: User message
            context: Retrieved context from memory
            **kwargs: Additional generation parameters

        Yields:
            Dict chunks with partial responses
        """
        try:
            # Preprocess
            processed_message = await self.preprocess(message)
            prompt = self._build_prompt(processed_message, context)

            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[Tuple[str, Any]] = asyncio.Queue()

            gen_temp = temperature if temperature is not None else self.config.get("temperature", 0.7)
            gen_tokens = max_tokens if max_tokens is not None else self.config.get("max_tokens", 2048)

            def run_stream() -> None:
                try:
                    for chunk in ollama.generate(
                        model=self.model,
                        prompt=prompt,
                        stream=True,
                        options={
                            "temperature": gen_temp,
                            "top_p": self.config.get("top_p", 0.9),
                            "num_predict": gen_tokens,
                        },
                    ):
                        loop.call_soon_threadsafe(queue.put_nowait, ("chunk", chunk))
                except Exception as exc:  # pragma: no cover - defensive guard
                    loop.call_soon_threadsafe(queue.put_nowait, ("error", exc))
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, ("done", None))

            worker = asyncio.create_task(asyncio.to_thread(run_stream))
            
            full_response = ""

            while True:
                kind, payload = await queue.get()
                if kind == "chunk":
                    text_chunk = payload["response"]
                    full_response += text_chunk
                    yield {
                        "text": text_chunk,
                        "done": payload.get("done", False),
                        "model_used": self.model,
                    }
                elif kind == "error":
                    await worker
                    raise payload
                elif kind == "done":
                    await worker
                    break

            await worker
            
            # Process tool calls in the complete response
            if self.tool_registry:
                processed_response, tool_results = await self._process_tool_calls(full_response)
                
                if tool_results:
                    # Yield tool processing indicator
                    yield {
                        "text": "\n[Processing tool results...]\n",
                        "done": False,
                        "model_used": self.model,
                    }
                    
                    # Re-generate with tool results (non-streaming for simplicity)
                    result = await self.generate(
                        message=processed_message,
                        context=context,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    
                    yield {
                        "text": result["response"],
                        "done": True,
                        "model_used": self.model,
                    }
                    
                    self._update_history(message, result["response"])
                    return
                else:
                    self._update_history(message, full_response)
            else:
                self._update_history(message, full_response)

        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            raise

    def _update_history(self, user_message: str, assistant_response: str):
        """Update conversation history."""
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })
        self.conversation_history.append({
            "role": "assistant", 
            "content": assistant_response,
        })
        
        # Trim history if too long
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

    async def preprocess(self, message: str) -> str:
        """
        Preprocess user message (override in subclasses)

        Args:
            message: Raw user message

        Returns:
            Processed message
        """
        return message

    async def postprocess(self, response: str) -> str:
        """
        Postprocess agent response (override in subclasses)

        Args:
            response: Raw agent response

        Returns:
            Processed response
        """
        return response

    def get_config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        config = self.config.copy()
        config["tools_enabled"] = self.enable_tools
        config["tools"] = self.tool_registry.list_tools() if self.tool_registry else []
        return config
