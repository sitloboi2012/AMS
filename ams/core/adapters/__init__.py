"""
Framework Adapters Module

This module provides adapters for different agent frameworks supported by the 
Agent Management Server. Each adapter implements a standardized interface for 
working with agents from specific frameworks such as AutoGen and CrewAI.

The module includes:
- A registry of available adapters for different frameworks
- A function to retrieve the appropriate adapter for a given framework
- Base and concrete adapter implementations
"""

import logging
from typing import Dict, Type

from ..registry.models import AgentFramework
from .base import FrameworkAdapter
from .autogen_adapter import AutoGenAdapter
from .crewai_adapter import CrewAIAdapter

logger = logging.getLogger(__name__)

# Registry of adapters for different frameworks
ADAPTER_REGISTRY: Dict[AgentFramework, Type[FrameworkAdapter]] = {
    AgentFramework.AUTOGEN: AutoGenAdapter,
    AgentFramework.CREWAI: CrewAIAdapter,
}

def get_adapter(framework: AgentFramework) -> FrameworkAdapter:
    """
    Get the appropriate adapter for a given framework.
    
    This function retrieves the appropriate adapter class from the registry
    and instantiates it. The adapter provides a standardized interface for
    working with agents from the specified framework.
    
    Args:
        framework: The agent framework type
        
    Returns:
        An instance of the appropriate framework adapter
        
    Raises:
        ValueError: If no adapter is available for the specified framework
    """
    logger.debug(f"Retrieving adapter for framework: {framework}")
    
    if framework not in ADAPTER_REGISTRY:
        error_msg = f"No adapter available for framework: {framework}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    adapter_class = ADAPTER_REGISTRY[framework]
    logger.debug(f"Using adapter class: {adapter_class.__name__}")
    
    return adapter_class()

def list_supported_frameworks() -> list[str]:
    """
    List all supported agent frameworks.
    
    Returns:
        A list of supported framework names
    """
    return [framework.value for framework in ADAPTER_REGISTRY.keys()]

__all__ = ["FrameworkAdapter", "AutoGenAdapter", "CrewAIAdapter", "get_adapter", "list_supported_frameworks"] 