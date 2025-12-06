"""
Base Agent class for all specialized agents
"""
import os
import logging
from typing import Optional, Dict, Any, AsyncGenerator
import yaml
from pathlib import Path
import ollama
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Load config
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "agent_configs.yaml"
with open(CONFIG_PATH, 'r') as f:
    CONFIG = yaml.safe_load(f)


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents
    """
    
    def __init__(self, agent_mode: str, model: Optional[str] = None):
        """
        Initialize the agent
        
        Args:
            agent_mode: Agent mode (general, math, code, writing, design)
            model: Model to use (defaults to configured model)
        """
        self.agent_mode = agent_mode
        self.config = CONFIG['agents'].get(agent_mode, CONFIG['agents']['general'])
        self.model = model or CONFIG['models']['default']
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        
        # Validate model exists
        try:
            ollama.show(self.model)
        except Exception as e:
            logger.warning(f"Model {self.model} not found: {e}")
            raise ValueError(f"Model '{self.model}' not installed. Please download it first.")
        
        logger.info(f"Initialized {agent_mode} agent with model {self.model}")
    
    def _build_prompt(self, message: str, context: str = "") -> str:
        """
        Build the complete prompt with system message and context
        
        Args:
            message: User message
            context: Retrieved context from memory
            
        Returns:
            Complete prompt string
        """
        system_prompt = self.config['system_prompt']
        
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
        **kwargs
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
            gen_temp = temperature if temperature is not None else self.config.get('temperature', 0.7)
            gen_tokens = max_tokens if max_tokens is not None else self.config.get('max_tokens', 2048)
            
            # Generate response
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': gen_temp,
                    'top_p': self.config.get('top_p', 0.9),
                    'num_predict': gen_tokens,
                }
            )
            
            # Postprocess response (can be overridden by subclasses)
            processed_response = await self.postprocess(response['response'])
            
            return {
                'response': processed_response,
                'model_used': self.model,
                'agent_mode': self.agent_mode,
                'tokens': response.get('tokens', 0)
            }
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise
    
    async def generate_stream(
        self, 
        message: str, 
        context: str = "",
        **kwargs
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
            
            # Stream response
            stream = ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=True,
                options={
                    'temperature': self.config.get('temperature', 0.7),
                    'top_p': self.config.get('top_p', 0.9),
                    'num_predict': self.config.get('max_tokens', 2048),
                }
            )
            
            for chunk in stream:
                yield {
                    'text': chunk['response'],
                    'done': chunk.get('done', False),
                    'model_used': self.model
                }
                
        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            raise
    
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
        return self.config