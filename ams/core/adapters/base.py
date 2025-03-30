"""
Framework Adapter Base Module

This module defines the base abstract class for framework adapters in the Agent Management Server.
Framework adapters provide a standardized interface for interacting with different agent frameworks.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..registry.models import AgentMetadata, AgentStatus

class FrameworkAdapter(ABC):
    """
    Abstract base class for framework adapters.
    
    Framework adapters provide a standardized interface for integrating different
    agent frameworks (such as AutoGen and CrewAI) with the Agent Management Server.
    Each concrete implementation handles the specifics of working with a particular
    framework while exposing a consistent interface.
    """
    
    @abstractmethod
    async def initialize_agent(self, metadata: AgentMetadata) -> Any:
        """
        Initialize an agent using the specific framework.
        
        Args:
            metadata: The agent metadata containing configuration information
            
        Returns:
            An initialized agent instance
            
        Raises:
            Exception: If initialization fails
        """
        pass

    @abstractmethod
    async def execute_agent(self, agent: Any, task: str, messages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute a task using the agent.
        
        Args:
            agent: The agent to execute the task
            task: The task description
            messages: Optional list of previous messages for context
            
        Returns:
            Dictionary containing execution results
            
        Raises:
            Exception: If execution fails
        """
        pass

    @abstractmethod
    async def get_agent_status(self, agent: Any) -> AgentStatus:
        """
        Get the current status of the agent.
        
        Args:
            agent: The agent to check
            
        Returns:
            The current status of the agent
            
        Raises:
            Exception: If status check fails
        """
        pass

    @abstractmethod
    async def terminate_agent(self, agent: Any) -> bool:
        """
        Terminate the agent.
        
        Args:
            agent: The agent to terminate
            
        Returns:
            True if termination is successful, False otherwise
            
        Raises:
            Exception: If termination fails
        """
        pass

    @abstractmethod
    async def get_agent_capabilities(self, agent: Any) -> Dict[str, Any]:
        """
        Get the capabilities of the agent.
        
        Args:
            agent: The agent to check capabilities for
            
        Returns:
            Dictionary containing capabilities information
            
        Raises:
            Exception: If capability retrieval fails
        """
        pass 