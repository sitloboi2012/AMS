"""
Communication Module

This module provides components for message exchange and collaboration between agents
in the Agent Management Server. It handles session management, message routing, and
conversation history.

Classes:
- CommunicationHub: Central hub for handling agent communication
- Message: Legacy message representation (deprecated)
- Session: Legacy session representation (deprecated)
- ChatMessage: Enhanced message representation with metadata
- ChatSession: Enhanced session management with formatting capabilities
"""

from .hub import CommunicationHub, Message
from .chat_context import ChatMessage, ChatSession

__all__ = [
    "CommunicationHub", 
    "Message", 
    "ChatMessage", 
    "ChatSession"
] 