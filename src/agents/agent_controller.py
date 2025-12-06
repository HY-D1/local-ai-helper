"""
Agent Controller - manages and routes requests to specialized agents
"""
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from src.agents.base_agent import BaseAgent
from src.agents.math_agent import MathAgent
from src.agents.code_agent import CodeAgent
from src.agents.writing_agent import WritingAgent
from src.agents.design_agent import DesignAgent

logger = logging.getLogger(__name__)


class AgentController:
    """
    Controller for managing multiple specialized agents
    """
    
    AGENT_CLASSES = {
        'general': BaseAgent,
        'math': MathAgent,
        'code': CodeAgent,
        'writing': WritingAgent,
        'design': DesignAgent
    }
    
    def __init__(self):
        """Initialize the agent controller"""
        self.agents: Dict[str, BaseAgent] = {}
        logger.info("AgentController initialized")
    
    def _get_agent(self, agent_mode: str, model: Optional[str] = None) -> BaseAgent:
        """
        Get or create agent for specified mode
        
        Args:
            agent_mode: Agent mode (general, math, code, writing, design)
            model: Model to use
            
        Returns:
            Agent instance
        """
        # For general mode, use BaseAgent directly
        if agent_mode == 'general':
            return BaseAgent(agent_mode=agent_mode, model=model)
        
        # Get agent class
        agent_class = self.AGENT_CLASSES.get(agent_mode)
        if not agent_class:
            logger.warning(f"Unknown agent mode: {agent_mode}, falling back to general")
            agent_class = BaseAgent
            agent_mode = 'general'
        
        # Create new agent instance
        return agent_class(agent_mode=agent_mode, model=model)
    
    async def generate(
        self,
        message: str,
        agent_mode: str = 'general',
        model: Optional[str] = None,
        context: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response using specified agent
        
        Args:
            message: User message
            agent_mode: Agent mode
            model: Model to use
            context: Retrieved context from memory
            **kwargs: Additional generation parameters
            
        Returns:
            Response dict
        """
        try:
            agent = self._get_agent(agent_mode, model)
            response = await agent.generate(message, context, **kwargs)
            logger.info(f"Generated response using {agent_mode} agent")
            return response
            
        except Exception as e:
            logger.error(f"Error in agent generation: {e}")
            raise
    
    async def generate_stream(
        self,
        message: str,
        agent_mode: str = 'general',
        model: Optional[str] = None,
        context: str = "",
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming response using specified agent
        
        Args:
            message: User message
            agent_mode: Agent mode
            model: Model to use
            context: Retrieved context from memory
            **kwargs: Additional generation parameters
            
        Yields:
            Response chunks
        """
        try:
            agent = self._get_agent(agent_mode, model)
            async for chunk in agent.generate_stream(message, context, **kwargs):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            raise
    
    def list_agents(self) -> Dict[str, Any]:
        """
        List available agents and their configs
        
        Returns:
            Dict of agent information
        """
        agents_info = {}
        for mode, agent_class in self.AGENT_CLASSES.items():
            if mode == 'general':
                agent = BaseAgent(agent_mode=mode)
            else:
                agent = agent_class(agent_mode=mode)
            config = agent.get_config()
            agents_info[mode] = {
                'name': config.get('name', mode),
                'description': config.get('description', ''),
                'class': agent_class.__name__
            }
        return agents_info