from abc import ABC, abstractmethod
from typing import List, Optional
from .models import AgentMetadata, AgentStatus

class AgentRegistry(ABC):
    @abstractmethod
    async def register_agent(self, agent: AgentMetadata) -> str:
        """Register a new agent in the registry."""
        pass

    @abstractmethod
    async def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """Retrieve an agent by its ID."""
        pass

    @abstractmethod
    async def list_agents(self) -> List[AgentMetadata]:
        """List all registered agents."""
        pass

    @abstractmethod
    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update the status of an agent."""
        pass

    @abstractmethod
    async def delete_agent(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        pass

    @abstractmethod
    async def find_agents_by_capability(self, capability_name: str) -> List[AgentMetadata]:
        """Find agents that have a specific capability."""
        pass 