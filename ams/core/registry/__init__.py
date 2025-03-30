"""
Agent Registry Module

This module provides components for managing agent metadata and registration
within the Agent Management Server. It handles the storage, retrieval, and
management of agent information.

Classes:
- AgentRegistry: Abstract base class defining the registry interface
- InMemoryAgentRegistry: In-memory implementation of the agent registry
- AgentMetadata: Data model for agent metadata
- AgentCapability: Representation of agent capabilities
- AgentFramework: Enumeration of supported agent frameworks
- AgentStatus: Enumeration of possible agent states
"""

from .base import AgentRegistry
from .memory import InMemoryAgentRegistry
from .models import AgentMetadata, AgentCapability, AgentFramework, AgentStatus

__all__ = [
    "AgentRegistry",
    "InMemoryAgentRegistry",
    "AgentMetadata",
    "AgentCapability",
    "AgentFramework",
    "AgentStatus"
] 