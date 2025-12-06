"""
Base Agent class for all specialized agents.
"""

import logging
import os
from abc import ABC
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

import ollama
import yaml

logger = logging.getLogger(__name__)

# Load config once at module import to avoid repeated disk reads
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "agent_configs.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""

    def __init__(
        self,
        agent_mode: str,
        model: Optional[str] = None,
        *,
        validate_model: Optional[bool] = None,
    ) -> None:
        """Initialize the agent.

        Args:
            agent_mode: Agent mode (general, math, code, writing, design).
            model: Model to use (defaults to configured model).
            validate_model: Whether to validate the model is installed. Defaults to
                the ``SKIP_MODEL_VALIDATION`` environment variable (False disables
                validation).
        """
        self.agent_mode = agent_mode
        self.config = CONFIG["agents"].get(agent_mode, CONFIG["agents"]["general"])
        self.model = model or CONFIG["models"]["default"]
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        env_validation = os.getenv("SKIP_MODEL_VALIDATION", "false").lower() not in (
            "1",
            "true",
            "yes",
        )
        self.validate_model = env_validation if validate_model is None else validate_model

        if self.validate_model:
            # Validate model exists once at initialization to avoid repeated
            # network calls during requests.
            try:
                ollama.show(self.model)
            except Exception as exc:  # noqa: BLE001 - surface validation errors
                logger.warning("Model %s not found: %s", self.model, exc)
                raise ValueError(
                    f"Model '{self.model}' not installed. Please download it first."
                ) from exc

        logger.info("Initialized %s agent with model %s", agent_mode, self.model)

    def _build_prompt(self, message: str, context: str = "") -> str:
        """Build the complete prompt with system message and context."""
        system_prompt = self.config["system_prompt"]

        if context:
            prompt = f"{system_prompt}\n\nRelevant Context:\n{context}\n\nUser: {message}"
        else:
            prompt = f"{system_prompt}\n\nUser: {message}"

        return prompt

    async def generate(
        self,
        message: str,
        context: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate a response."""
        try:
            # Preprocess message (can be overridden by subclasses)
            processed_message = await self.preprocess(message)

            # Build prompt
            prompt = self._build_prompt(processed_message, context)

            # Use provided params or fall back to config
            gen_temp = temperature if temperature is not None else self.config.get(
                "temperature", 0.7
            )
            gen_tokens = max_tokens if max_tokens is not None else self.config.get(
                "max_tokens", 2048
            )

            # Generate response (Ollama client is synchronous)
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": gen_temp,
                    "top_p": self.config.get("top_p", 0.9),
                    "num_predict": gen_tokens,
                },
            )

            # Postprocess response (can be overridden by subclasses)
            processed_response = await self.postprocess(response["response"])

            return {
                "response": processed_response,
                "model_used": self.model,
                "agent_mode": self.agent_mode,
                "tokens": response.get("tokens", 0),
            }

        except Exception as exc:  # noqa: BLE001 - preserve stack for debugging
            logger.error("Generation error: %s", exc)
            raise

    async def generate_stream(
        self,
        message: str,
        context: str = "",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a streaming response."""
        try:
            # Preprocess
            processed_message = await self.preprocess(message)
            prompt = self._build_prompt(processed_message, context)

            # Stream response
            stream = ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=True,
                options={
                    "temperature": self.config.get("temperature", 0.7),
                    "top_p": self.config.get("top_p", 0.9),
                    "num_predict": self.config.get("max_tokens", 2048),
                },
            )

            for chunk in stream:
                yield {
                    "text": chunk["response"],
                    "done": chunk.get("done", False),
                    "model_used": self.model,
                }

        except Exception as exc:  # noqa: BLE001 - preserve stack for debugging
            logger.error("Stream generation error: %s", exc)
            raise

    async def preprocess(self, message: str) -> str:
        """Preprocess user message (override in subclasses)."""
        return message

    async def postprocess(self, response: str) -> str:
        """Postprocess agent response (override in subclasses)."""
        return response

    def get_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self.config
