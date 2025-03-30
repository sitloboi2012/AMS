"""
API Models

This module contains the dataclass models used for API requests and responses.
These models define the expected data structures for the API endpoints.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class AgentCapabilityModel:
    """
    Represents a capability that an agent can possess.
    
    Attributes:
        name: The name of the capability
        description: A description of what the capability does
        parameters: Optional configuration parameters for the capability
    """
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class AgentRegistrationRequest:
    """
    Request model for registering a new agent.
    
    Attributes:
        name: The name of the agent
        description: A description of the agent's purpose
        system_prompt: The system prompt that defines the agent's behavior
        framework: The framework the agent uses (e.g., "autogen", "crewai")
        capabilities: Optional list of capabilities the agent possesses
        config: Optional configuration parameters for the agent
    """
    name: str
    description: str
    system_prompt: str
    framework: str
    capabilities: Optional[List[AgentCapabilityModel]] = None
    config: Optional[Dict[str, Any]] = None


@dataclass
class AgentResponse:
    """
    Response model for agent information.
    
    Attributes:
        id: Unique identifier for the agent
        name: The name of the agent
        description: A description of the agent's purpose
        framework: The framework the agent uses
        status: Current status of the agent
        created_at: Timestamp when the agent was created
        updated_at: Timestamp when the agent was last updated
    """
    id: str
    name: str
    description: str
    framework: str
    status: str
    created_at: str
    updated_at: str


@dataclass
class TaskRequest:
    """
    Request model for creating a new task.
    
    Attributes:
        task: The description of the task to be performed
    """
    task: str


@dataclass
class TaskResponse:
    """
    Response model for task creation.
    
    Attributes:
        session_id: Unique identifier for the task session
        task: The description of the task
        agents: List of agent IDs assigned to the task
        status: Current status of the task
    """
    session_id: str
    task: str
    agents: List[str]
    status: str = "created"


@dataclass
class MessageRequest:
    """
    Request model for sending a message.
    
    Attributes:
        content: The content of the message
        sender_id: ID of the sender
        sender_name: Name of the sender
        metadata: Optional additional information about the message
    """
    content: str
    sender_id: str
    sender_name: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MessageResponse:
    """
    Response model for message information.
    
    Attributes:
        message_id: Unique identifier for the message
        content: The content of the message
        sender_id: ID of the sender
        sender_name: Name of the sender
        timestamp: When the message was sent
        metadata: Optional additional information about the message
    """
    message_id: str
    content: str
    sender_id: str
    sender_name: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None 