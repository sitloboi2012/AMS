"""
Error Handling Module

This module defines custom exceptions for the Agent Management Server.
Using specific exception types helps in better error handling and provides
clearer error messages to clients.
"""

from typing import Any, Dict, Optional


class AMSBaseException(Exception):
    """
    Base exception class for all AMS exceptions.
    
    Attributes:
        message: Human-readable error message
        code: Error code for this type of error
        details: Additional details about the error
    """
    def __init__(
        self, 
        message: str, 
        code: str = "AMS_ERROR", 
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for API responses."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


# Registry Exceptions
class RegistryException(AMSBaseException):
    """Base exception for registry-related errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="REGISTRY_ERROR", details=details)


class AgentNotFoundException(RegistryException):
    """Exception raised when an agent is not found in the registry."""
    def __init__(self, agent_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Agent with ID '{agent_id}' not found"
        super().__init__(message, details=details)


class AgentAlreadyExistsException(RegistryException):
    """Exception raised when attempting to register an agent that already exists."""
    def __init__(self, agent_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Agent with ID '{agent_id}' already exists"
        super().__init__(message, details=details)


class InvalidAgentDataException(RegistryException):
    """Exception raised when agent data is invalid."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details=details)


# Framework Adapter Exceptions
class AdapterException(AMSBaseException):
    """Base exception for adapter-related errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="ADAPTER_ERROR", details=details)


class UnsupportedFrameworkException(AdapterException):
    """Exception raised when a framework is not supported."""
    def __init__(self, framework: str, details: Optional[Dict[str, Any]] = None):
        message = f"Framework '{framework}' is not supported"
        super().__init__(message, details=details)


class AgentInitializationError(AdapterException):
    """Exception raised when an agent cannot be initialized."""
    def __init__(self, agent_id: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to initialize agent '{agent_id}': {reason}"
        super().__init__(message, details=details)


class ExecutionError(AdapterException):
    """Exception raised when agent execution fails."""
    def __init__(self, agent_id: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Execution failed for agent '{agent_id}': {reason}"
        super().__init__(message, details=details)


# Supervisor Exceptions
class SupervisorException(AMSBaseException):
    """Base exception for supervisor-related errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="SUPERVISOR_ERROR", details=details)


class SessionNotFoundException(SupervisorException):
    """Exception raised when a session is not found."""
    def __init__(self, session_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Session with ID '{session_id}' not found"
        super().__init__(message, details=details)


class InvalidTaskException(SupervisorException):
    """Exception raised when a task is invalid."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details=details)


class NoSuitableAgentsException(SupervisorException):
    """Exception raised when no suitable agents are found for a task."""
    def __init__(self, task: str, details: Optional[Dict[str, Any]] = None):
        message = f"No suitable agents found for task: {task}"
        super().__init__(message, details=details)


# Communication Exceptions
class CommunicationException(AMSBaseException):
    """Base exception for communication-related errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="COMMUNICATION_ERROR", details=details)


class MessageDeliveryError(CommunicationException):
    """Exception raised when a message cannot be delivered."""
    def __init__(self, session_id: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to deliver message to session '{session_id}': {reason}"
        super().__init__(message, details=details)


class SessionClosedException(CommunicationException):
    """Exception raised when trying to use a closed session."""
    def __init__(self, session_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Session '{session_id}' is closed and cannot receive messages"
        super().__init__(message, details=details) 