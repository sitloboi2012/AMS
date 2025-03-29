"""
Framework adapters for different agent frameworks.
"""

from typing import Dict, Type

from ..registry.models import AgentFramework
from .base import FrameworkAdapter
from .autogen_adapter import AutoGenAdapter
from .crewai_adapter import CrewAIAdapter

# Registry of adapters for different frameworks
ADAPTER_REGISTRY: Dict[AgentFramework, Type[FrameworkAdapter]] = {
    AgentFramework.AUTOGEN: AutoGenAdapter,
    AgentFramework.CREWAI: CrewAIAdapter,
}

def get_adapter(framework: AgentFramework) -> FrameworkAdapter:
    """
    Get the appropriate adapter for a given framework.
    
    Args:
        framework: The agent framework type
        
    Returns:
        An instance of the appropriate framework adapter
        
    Raises:
        ValueError: If no adapter is available for the specified framework
    """
    if framework not in ADAPTER_REGISTRY:
        raise ValueError(f"No adapter available for framework: {framework}")
    
    adapter_class = ADAPTER_REGISTRY[framework]
    return adapter_class()

__all__ = ["FrameworkAdapter", "AutoGenAdapter", "CrewAIAdapter", "get_adapter"] 