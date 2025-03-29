import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..registry.models import AgentMetadata

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
    """
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
    
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
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = Session(
            session_id=session_id,
            task=task,
            agents=agents
        )
        
        logger.info(f"Created session {session_id} with {len(agents)} agents for task: {task}")
        return session_id
    
    def send_message(
        self, 
        session_id: str, 
        content: str, 
        sender_id: str,
        sender_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
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
            raise ValueError(f"Session {session_id} not found")
        
        message = Message(
            content=content,
            sender_id=sender_id,
            sender_name=sender_name,
            metadata=metadata
        )
        
        self.sessions[session_id].add_message(message)
        logger.info(f"Message sent in session {session_id} by {sender_name}")
        
        return message
    
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
            raise ValueError(f"Session {session_id} not found")
        
        return self.sessions[session_id].get_history()
    
    def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a collaboration session.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if the session was terminated successfully
            
        Raises:
            ValueError: If the session doesn't exist
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        self.sessions[session_id].active = False
        logger.info(f"Session {session_id} terminated")
        
        return True
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions.
        
        Returns:
            List of session details
        """
        return [session.to_dict() for session in self.sessions.values()] 