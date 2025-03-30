"""
Supervisor Module

This module provides components for orchestrating and managing agent collaborations
in the Agent Management Server. It handles task delegation, coordination between agents,
and supervision of collaborative workflows.

Classes:
- SupervisorAgent: Agent responsible for orchestrating multi-agent collaborations
- SupervisorManager: Manager for creating and handling supervisor agents
"""

from .base import SupervisorAgent
from .manager import SupervisorManager

__all__ = ["SupervisorAgent", "SupervisorManager"] 