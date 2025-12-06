"""
Agent Controller - manages and routes requests to specialized agents.
"""

import logging
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

import yaml

from src.agents.base_agent import BaseAgent
from src.agents.code_agent import CodeAgent
from src.agents.design_agent import DesignAgent
from src.agents.math_agent import MathAgent
from src.agents.writing_agent import WritingAgent

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "agent_configs.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)


class AgentController:
    """Controller for managing multiple specialized agents."""

    AGENT_CLASSES = {
        "general": BaseAgent,
        "math": MathAgent,
        "code": CodeAgent,
        "writing": WritingAgent,
        "design": DesignAgent,
    }

    def __init__(self, *, validate_models: Optional[bool] = None) -> None:
        """Initialize the agent controller."""
        self.agents: Dict[Tuple[str, str], BaseAgent] = {}
        env_validation = os.getenv("SKIP_MODEL_VALIDATION", "false").lower() not in (
            "1",
            "true",
            "yes",
        )
        self.validate_models = env_validation if validate_models is None else validate_models
        logger.info("AgentController initialized")

    def _resolve_key(self, agent_mode: str, model: Optional[str]) -> Tuple[str, str]:
        resolved_mode = agent_mode if agent_mode in self.AGENT_CLASSES else "general"
        resolved_model = model or CONFIG["models"]["default"]
        return resolved_mode, resolved_model

    def _get_agent(self, agent_mode: str, model: Optional[str] = None) -> BaseAgent:
        """Get or create an agent for the specified mode."""
        resolved_mode, resolved_model = self._resolve_key(agent_mode, model)
        cache_key = (resolved_mode, resolved_model)

        if cache_key not in self.agents:
            agent_class = self.AGENT_CLASSES.get(resolved_mode, BaseAgent)
            self.agents[cache_key] = agent_class(
                agent_mode=resolved_mode,
                model=resolved_model,
                validate_model=self.validate_models,
            )
        return self.agents[cache_key]

    async def generate(
        self,
        message: str,
        agent_mode: str = "general",
        model: Optional[str] = None,
        context: str = "",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate response using specified agent."""
        agent = self._get_agent(agent_mode, model)
        try:
            response = await agent.generate(message, context, **kwargs)
            logger.info("Generated response using %s agent", agent_mode)
            return response
        except Exception as exc:  # noqa: BLE001 - preserve stack
            logger.error("Error in agent generation: %s", exc)
            raise

    async def generate_stream(
        self,
        message: str,
        agent_mode: str = "general",
        model: Optional[str] = None,
        context: str = "",
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming response using specified agent."""
        agent = self._get_agent(agent_mode, model)
        try:
            async for chunk in agent.generate_stream(message, context, **kwargs):
                yield chunk
        except Exception as exc:  # noqa: BLE001
            logger.error("Error in stream generation: %s", exc)
            raise

    def list_agents(self) -> Dict[str, Any]:
        """List available agents and their configs."""
        agents_info: Dict[str, Any] = {}
        for mode, agent_class in self.AGENT_CLASSES.items():
            agent = self._get_agent(mode)
            config = agent.get_config()
            agents_info[mode] = {
                "name": config.get("name", mode),
                "description": config.get("description", ""),
                "class": agent_class.__name__,
            }
        return agents_info
