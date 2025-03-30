"""
Communication Hub Module

This module provides the CommunicationHub class, which manages message exchange
between agents in collaboration sessions. It handles session creation, message passing,
and history retrieval.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..registry.models import AgentMetadata
from .chat_context import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

class Message:
    """Represents a message in a collaboration session."""
    
    def __init__(
        self,
        content: str,
        sender_id: str,
        sender_name: str,
        timestamp: Optional[str] = None,
        message_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.timestamp = timestamp or datetime.now().isoformat()
        self.message_id = message_id or str(uuid.uuid4())
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "message_id": self.message_id,
            "content": self.content,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class Session:
    """Represents a collaboration session between agents."""
    
    def __init__(
        self, 
        session_id: str,
        task: str,
        agents: List[AgentMetadata],
        created_at: Optional[str] = None
    ):
        self.session_id = session_id
        self.task = task
        self.agents = agents
        self.messages: List[Message] = []
        self.created_at = created_at or datetime.now().isoformat()
        self.active = True
    
    def add_message(self, message: Message) -> None:
        """Add a message to the session."""
        self.messages.append(message)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the message history for this session."""
        return [message.to_dict() for message in self.messages]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the session to a dictionary."""
        return {
            "session_id": self.session_id,
            "task": self.task,
            "agents": [agent.id for agent in self.agents],
            "created_at": self.created_at,
            "active": self.active,
            "message_count": len(self.messages)
        }


class CommunicationHub:
    """
    Manages communication between agents in collaboration sessions.
    
    This class serves as the central communication mechanism for the Agent Management Server,
    handling message routing between agents, session management, and history tracking.
    """
    
    def __init__(self):
        """Initialize a new CommunicationHub."""
        self.sessions: Dict[str, ChatSession] = {}
        logger.info("CommunicationHub initialized")
    
    def create_session(
        self, 
        task: str, 
        agents: List[AgentMetadata]
    ) -> str:
        """
        Create a new collaboration session.
        
        Args:
            task: The task description
            agents: List of agents participating in the session
            
        Returns:
            The session ID
            
        Raises:
            ValueError: If agents list is empty
        """
        if not agents:
            logger.error("Cannot create session with empty agents list")
            raise ValueError("Cannot create session with empty agents list")
            
        session_id = str(uuid.uuid4())
        
        try:
            # Extract agent IDs for metadata
            agent_ids = [agent.id for agent in agents]
            
            # Create a new chat session
            self.sessions[session_id] = ChatSession(
                session_id=session_id,
                metadata={"agents": agent_ids},
                task=task
            )
            
            # Add a system message to start the session
            self.send_message(
                session_id=session_id,
                content=f"Session started with task: {task}",
                sender_id="system",
                sender_name="System",
                metadata={"type": "system", "action": "session_start"}
            )
            
            logger.info(f"Created session {session_id} with {len(agents)} agents for task: {task}")
            return session_id
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    def send_message(
        self, 
        session_id: str, 
        content: str, 
        sender_id: str,
        sender_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Send a message in a session.
        
        Args:
            session_id: The session ID
            content: The message content
            sender_id: The ID of the sending agent
            sender_name: The name of the sending agent
            metadata: Optional metadata for the message
            
        Returns:
            The created message
            
        Raises:
            ValueError: If the session doesn't exist
        """
        if session_id not in self.sessions:
            error_msg = f"Session {session_id} not found"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Determine sender role and framework for metadata
            sender_role = "agent"
            sender_framework = None
            
            if sender_id == "system":
                sender_role = "system"
            elif metadata and "type" in metadata:
                msg_type = metadata["type"]
                if msg_type == "system":
                    sender_role = "system"
                
                # Try to extract framework info if available
                if "framework" in metadata:
                    sender_framework = metadata["framework"]
            
            # Update metadata with role and framework info
            message_metadata = metadata.copy() if metadata else {}
            message_metadata["sender_role"] = sender_role
            if sender_framework:
                message_metadata["sender_framework"] = sender_framework
            
            # Generate a unique message ID
            message_id = str(uuid.uuid4())
            
            # Create a new chat message with all attributes properly set
            message = ChatMessage(
                content=content,
                sender_id=sender_id,
                sender_name=sender_name,
                metadata=message_metadata,
                message_id=message_id,
                sender_role=sender_role,
                sender_framework=sender_framework
            )
            
            # Add the message to the session
            self.sessions[session_id].add_message(message)
            logger.info(f"Message sent in session {session_id} by {sender_name} [{sender_id}]")
            
            return message
        except Exception as e:
            logger.error(f"Error sending message in session {session_id}: {str(e)}")
            raise
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get the message history for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of messages in the session
            
        Raises:
            ValueError: If the session doesn't exist
        """
        if session_id not in self.sessions:
            error_msg = f"Session {session_id} not found"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Convert all messages to dictionaries
            messages = []
            for msg in self.sessions[session_id].get_messages():
                try:
                    msg_dict = msg.to_dict()
                    messages.append(msg_dict)
                except Exception as e:
                    # Create a safe fallback dictionary if conversion fails
                    logger.error(f"Error converting message to dict: {str(e)}")
                    safe_dict = {
                        "message_id": str(uuid.uuid4()),
                        "content": getattr(msg, "content", "Error: content not available"),
                        "sender_id": getattr(msg, "sender_id", "unknown"),
                        "sender_name": getattr(msg, "sender_name", "Unknown"),
                        "sender_role": getattr(msg, "sender_role", "agent"),
                        "sender_framework": getattr(msg, "sender_framework", None),
                        "timestamp": datetime.now().isoformat(),
                        "metadata": getattr(msg, "metadata", {})
                    }
                    messages.append(safe_dict)
            
            logger.debug(f"Retrieved {len(messages)} messages from session {session_id}")
            return messages
        except Exception as e:
            logger.error(f"Error retrieving session history: {str(e)}")
            return []  # Return empty list on error
    
    def get_session(self, session_id: str) -> ChatSession:
        """
        Get a session by ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            The chat session
            
        Raises:
            ValueError: If the session doesn't exist
        """
        if session_id not in self.sessions:
            error_msg = f"Session {session_id} not found"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        return self.sessions[session_id]
    
    def get_formatted_history(
        self, 
        session_id: str, 
        exclude_sender_ids: Optional[List[str]] = None, 
        include_framework: bool = False,
        max_messages: Optional[int] = None
    ) -> str:
        """
        Get a formatted string of the conversation history suitable for prompts.
        
        Args:
            session_id: The session ID
            exclude_sender_ids: Optional list of sender IDs to exclude from the history
            include_framework: Whether to include framework information in message display
            max_messages: Maximum number of messages to include in the history
            
        Returns:
            Formatted conversation history
            
        Raises:
            ValueError: If the session doesn't exist
        """
        if session_id not in self.sessions:
            error_msg = f"Session {session_id} not found"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Convert list to set if provided
            exclude_senders = set(exclude_sender_ids) if exclude_sender_ids else None
            
            return self.sessions[session_id].get_formatted_history(
                exclude_senders=exclude_senders,
                include_framework=include_framework,
                max_messages=max_messages
            )
        except Exception as e:
            logger.error(f"Error formatting history for session {session_id}: {str(e)}")
            return "\n\n### CONVERSATION HISTORY ###\n\n[Error retrieving conversation history]\n\n"
    
    def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a collaboration session.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If the session doesn't exist
        """
        if session_id not in self.sessions:
            error_msg = f"Session {session_id} not found"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Mark the session as inactive instead of removing it
            self.sessions[session_id].is_active = False
            
            # Add a system message about termination
            self.send_message(
                session_id=session_id,
                content="Session terminated",
                sender_id="system",
                sender_name="System",
                metadata={"type": "system", "action": "session_terminate"}
            )
            
            logger.info(f"Terminated session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error terminating session {session_id}: {str(e)}")
            return False
    
    def list_sessions(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        List all sessions.
        
        Args:
            include_inactive: Whether to include inactive sessions
            
        Returns:
            List of session details
        """
        try:
            sessions = []
            for session_id, session in self.sessions.items():
                # Skip inactive sessions unless requested
                if not include_inactive and not session.is_active:
                    continue
                    
                sessions.append(session.get_session_info())
            
            logger.debug(f"Listed {len(sessions)} sessions")
            return sessions
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            return []
            
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session completely.
        
        This is different from terminate_session which just marks as inactive.
        This method actually removes the session from memory.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if successful, False otherwise
        """
        if session_id not in self.sessions:
            logger.warning(f"Attempted to delete non-existent session {session_id}")
            return False
            
        try:
            del self.sessions[session_id]
            logger.info(f"Deleted session {session_id} from memory")
            return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False 