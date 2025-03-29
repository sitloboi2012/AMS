from abc import ABC, abstractmethod
from typing import Dict, Any
from ..registry.models import AgentMetadata, AgentStatus

class FrameworkAdapter(ABC):
    @abstractmethod
    async def initialize_agent(self, metadata: AgentMetadata) -> Any:
        """Initialize an agent using the specific framework."""
        pass

    @abstractmethod
    async def execute_agent(self, agent: Any, task: str) -> Dict[str, Any]:
        """Execute a task using the agent."""
        pass

    @abstractmethod
    async def get_agent_status(self, agent: Any) -> AgentStatus:
        """Get the current status of the agent."""
        pass

    @abstractmethod
    async def terminate_agent(self, agent: Any) -> bool:
        """Terminate the agent."""
        pass

    @abstractmethod
    async def get_agent_capabilities(self, agent: Any) -> Dict[str, Any]:
        """Get the capabilities of the agent."""
        pass 