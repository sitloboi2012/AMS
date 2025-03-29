from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..registry.models import AgentMetadata

class SupervisorAgent(ABC):
    @abstractmethod
    async def analyze_task(self, task: str) -> Dict[str, Any]:
        """Analyze the task and determine required capabilities."""
        pass

    @abstractmethod
    async def select_agents(self, task_analysis: Dict[str, Any]) -> List[AgentMetadata]:
        """Select appropriate agents based on task analysis."""
        pass

    @abstractmethod
    async def create_collaboration(self, agents: List[AgentMetadata], task: str) -> str:
        """Create a new collaboration session with selected agents."""
        pass

    @abstractmethod
    async def monitor_collaboration(self, session_id: str) -> Dict[str, Any]:
        """Monitor the status and progress of a collaboration session."""
        pass

    @abstractmethod
    async def terminate_collaboration(self, session_id: str) -> bool:
        """Terminate a collaboration session."""
        pass 