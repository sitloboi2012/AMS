import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from .base import AgentRegistry
from .models import AgentMetadata, AgentStatus, AgentCapability

logger = logging.getLogger(__name__)

class InMemoryAgentRegistry(AgentRegistry):
    """
    In-memory implementation of the AgentRegistry.
    Stores agents in a dictionary with agent ID as the key.
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentMetadata] = {}
    
    async def register_agent(self, agent: AgentMetadata) -> str:
        """
        Register a new agent in the registry.
        
        Args:
            agent: The agent metadata to register
            
        Returns:
            The ID of the registered agent
        """
        # If agent doesn't have an ID, generate one
        if not agent.id:
            agent.id = str(uuid.uuid4())
        
        # Update timestamps
        current_time = datetime.now().isoformat()
        agent.created_at = current_time
        agent.updated_at = current_time
        
        # Store the agent
        self.agents[agent.id] = agent
        
        logger.info(f"Registered agent: {agent.name} ({agent.id})")
        return agent.id
    
    async def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """
        Retrieve an agent by its ID.
        
        Args:
            agent_id: The ID of the agent to retrieve
            
        Returns:
            The agent metadata, or None if not found
        """
        return self.agents.get(agent_id)
    
    async def list_agents(self) -> List[AgentMetadata]:
        """
        List all registered agents.
        
        Returns:
            List of all registered agents
        """
        return list(self.agents.values())
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """
        Update the status of an agent.
        
        Args:
            agent_id: The ID of the agent to update
            status: The new status
            
        Returns:
            True if the agent was updated, False if the agent wasn't found
            
        Raises:
            ValueError: If the agent doesn't exist
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Update the agent status
        self.agents[agent_id].status = status
        self.agents[agent_id].updated_at = datetime.now().isoformat()
        
        logger.info(f"Updated agent {agent_id} status to {status}")
        return True
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the registry.
        
        Args:
            agent_id: The ID of the agent to remove
            
        Returns:
            True if the agent was removed, False if the agent wasn't found
        """
        if agent_id not in self.agents:
            return False
        
        # Remove the agent
        del self.agents[agent_id]
        
        logger.info(f"Deleted agent: {agent_id}")
        return True
    
    async def find_agents_by_capability(self, capability_name: str) -> List[AgentMetadata]:
        """
        Find agents that have a specific capability.
        
        Args:
            capability_name: The name of the capability
            
        Returns:
            List of agents that have the capability
        """
        matching_agents = []
        
        for agent in self.agents.values():
            # Skip agents that are not ready
            if agent.status != AgentStatus.READY:
                continue
            
            # If agent has no capabilities defined, skip
            if not agent.capabilities:
                continue
            
            # Check if any capability matches
            for capability in agent.capabilities:
                if capability.name == capability_name:
                    matching_agents.append(agent)
                    break
        
        logger.info(f"Found {len(matching_agents)} agents with capability: {capability_name}")
        return matching_agents
    
    async def find_agents_by_framework(self, framework) -> List[AgentMetadata]:
        """
        Find agents of a specific framework.
        
        Args:
            framework: The framework to search for
            
        Returns:
            List of agents that use the specified framework
        """
        matching_agents = [
            agent for agent in self.agents.values() 
            if agent.framework == framework
        ]
        
        logger.info(f"Found {len(matching_agents)} agents with framework: {framework}")
        return matching_agents 