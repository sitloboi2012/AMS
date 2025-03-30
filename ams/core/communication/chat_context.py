"""
Classes for managing chat history and context between agents.

This module provides classes for representing and managing chat messages and sessions
in the Agent Management Server. It handles the persistence and formatting of conversation
history between different agents.
"""

import logging
from typing import List, Dict, Any, Optional, Set, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ChatMessage:
    """
    Represents a single message in a chat history.
    
    This class encapsulates all metadata and content for messages exchanged
    between agents, maintaining information about sender, timestamps, 
    and additional context.
    """
    def __init__(
        self, 
        content: str, 
        sender_id: str, 
        sender_name: Optional[str] = None,
        timestamp: Optional[Union[datetime, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
        sender_role: str = "agent",
        sender_framework: Optional[str] = None
    ):
        """Initialize a new chat message.
        
        Args:
            content: The message content
            sender_id: Unique identifier for the sender
            sender_name: Display name for the sender (defaults to sender_id if not provided)
            timestamp: When the message was sent (defaults to now if not provided)
            metadata: Additional information about the message
            message_id: Unique identifier for the message (defaults to a UUID if not provided)
            sender_role: Role of the sender (defaults to "agent")
            sender_framework: Framework of the sender (defaults to None)
        """
        self.content = content
        self.sender_id = sender_id
        self.sender_name = sender_name or sender_id
        
        # Handle timestamp conversion
        if timestamp is None:
            self.timestamp = datetime.now()
        elif isinstance(timestamp, str):
            try:
                self.timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                logger.warning(f"Invalid timestamp format: {timestamp}, using current time")
                self.timestamp = datetime.now()
        else:
            self.timestamp = timestamp
            
        self.metadata = metadata or {}
        self.message_id = message_id or str(uuid.uuid4())
        self.sender_role = sender_role
        self.sender_framework = sender_framework

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.
        
        Returns:
            Dict containing all message attributes
        """
        try:
            timestamp_str = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp)
            
            return {
                "message_id": self.message_id,
                "content": self.content,
                "sender_id": self.sender_id,
                "sender_name": self.sender_name,
                "sender_role": self.sender_role,
                "sender_framework": self.sender_framework,
                "timestamp": timestamp_str,
                "metadata": self.metadata
            }
        except Exception as e:
            logger.error(f"Error converting message to dictionary: {str(e)}")
            # Return a minimal safe dictionary if conversion fails
            return {
                "message_id": self.message_id or str(uuid.uuid4()),
                "content": getattr(self, "content", "Error: content not available"),
                "sender_id": getattr(self, "sender_id", "unknown"),
                "sender_name": getattr(self, "sender_name", "Unknown"),
                "timestamp": datetime.now().isoformat(),
                "metadata": {}
            }
    
    def format_for_prompt(self, include_framework: bool = False) -> str:
        """
        Format the message for inclusion in a prompt.
        
        Creates a string representation of the message suitable for
        inclusion in a prompt to be sent to an LLM.
        
        Args:
            include_framework: Whether to include framework information
            
        Returns:
            Formatted message string
        """
        try:
            framework_info = ""
            if include_framework:
                # Check both direct attribute and metadata for framework info
                framework = None
                if hasattr(self, 'sender_framework') and self.sender_framework:
                    framework = self.sender_framework
                elif self.metadata and "framework" in self.metadata:
                    framework = self.metadata["framework"]
                
                if framework:
                    framework_info = f" [Framework: {framework}]"
                
            return f"## Message from {self.sender_name}{framework_info}:\n{self.content}"
        except Exception as e:
            logger.error(f"Error formatting message for prompt: {str(e)}")
            return f"## Message from {getattr(self, 'sender_name', 'Unknown')}:\n{getattr(self, 'content', 'Content unavailable')}"


class ChatSession:
    """
    Manages the full conversation context for a collaboration session.
    
    This class stores and organizes messages exchanged during a collaboration session,
    providing methods to retrieve and format conversation history.
    """
    def __init__(
        self, 
        session_id: str, 
        metadata: Dict[str, Any], 
        task: str = "",
        messages: Optional[List[ChatMessage]] = None,
        created_at: Optional[str] = None
    ):
        """
        Initialize a new chat session.
        
        Args:
            session_id: Unique identifier for the session
            metadata: Additional information about the session
            task: The task description for this session
            messages: Initial messages in the session
            created_at: When the session was created (ISO format string)
        """
        self.session_id = session_id
        self.metadata = metadata or {}
        self.task = task
        self.messages = messages or []
        self.start_time = datetime.now()
        self.is_active = True
        
        # Handle created_at conversion
        if created_at is None:
            self.created_at = datetime.now().isoformat()
        else:
            self.created_at = created_at
    
    def add_message(self, message: ChatMessage) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            message: The ChatMessage to add to the session
        """
        if not isinstance(message, ChatMessage):
            logger.warning(f"Expected ChatMessage object, got {type(message).__name__}")
            return
            
        self.messages.append(message)
        logger.debug(f"Added message from {message.sender_name} to session {self.session_id}")
    
    def get_messages(self) -> List[ChatMessage]:
        """
        Get all messages in the session.
        
        Returns:
            List of all ChatMessage objects in the session
        """
        return self.messages
    
    def get_messages_by_sender(self, sender_id: str) -> List[ChatMessage]:
        """
        Get all messages from a specific sender.
        
        Args:
            sender_id: The ID of the sender to filter by
            
        Returns:
            List of ChatMessage objects from the specified sender
        """
        return [msg for msg in self.messages if msg.sender_id == sender_id]
    
    def get_formatted_history(
        self, 
        exclude_senders: Optional[Set[str]] = None,
        include_framework: bool = False,
        max_messages: Optional[int] = None,
        max_chars_per_message: int = 5000
    ) -> str:
        """
        Get a formatted string of the conversation history.
        
        Args:
            exclude_senders: Set of sender IDs to exclude
            include_framework: Whether to include framework information
            max_messages: Maximum number of messages to include
            max_chars_per_message: Maximum characters per message to include
            
        Returns:
            Formatted conversation history as a string
        """
        try:
            exclude_senders = exclude_senders or set(["system"])
            
            # Filter messages
            filtered_messages = [
                msg for msg in self.messages 
                if msg.sender_id not in exclude_senders
            ]
            
            # Limit to max_messages if specified
            if max_messages and len(filtered_messages) > max_messages:
                filtered_messages = filtered_messages[-max_messages:]
            
            # Format each message
            formatted = "\n\n### CONVERSATION HISTORY ###\n\n"
            for msg in filtered_messages:
                try:
                    # Limit very long messages
                    content = msg.content
                    if len(content) > max_chars_per_message:
                        content_preview = content[:max_chars_per_message]
                        logger.info(f"Message from {msg.sender_name} truncated (length: {len(content)})")
                        msg.content = f"{content_preview}... [truncated, {len(content)} chars total]"
                    
                    formatted += msg.format_for_prompt(include_framework=include_framework) + "\n\n"
                except Exception as e:
                    logger.error(f"Error formatting message: {str(e)}")
                    # Skip problematic messages
            
            return formatted
        except Exception as e:
            logger.error(f"Error generating formatted history: {str(e)}")
            return "\n\n### CONVERSATION HISTORY ###\n\n[Error retrieving conversation history]\n\n"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the session to a dictionary.
        
        Returns:
            Dictionary representation of the session
        """
        try:
            return {
                "session_id": self.session_id,
                "task": self.task,
                "messages": [msg.to_dict() for msg in self.messages],
                "metadata": self.metadata,
                "created_at": self.created_at,
                "is_active": self.is_active
            }
        except Exception as e:
            logger.error(f"Error converting session to dictionary: {str(e)}")
            # Return a minimal safe dictionary if conversion fails
            return {
                "session_id": self.session_id,
                "task": getattr(self, "task", ""),
                "messages": [],
                "metadata": {},
                "created_at": datetime.now().isoformat(),
                "is_active": False
            }

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the session.
        
        Returns:
            Dictionary with session information
        """
        try:
            unique_senders = set(msg.sender_id for msg in self.messages if msg.sender_id != "system")
            
            return {
                "session_id": self.session_id,
                "start_time": self.start_time.isoformat(),
                "message_count": len(self.messages),
                "unique_participants": len(unique_senders),
                "is_active": self.is_active,
                "metadata": self.metadata
            }
        except Exception as e:
            logger.error(f"Error getting session info: {str(e)}")
            return {
                "session_id": self.session_id,
                "error": "Failed to retrieve complete session info"
            } 