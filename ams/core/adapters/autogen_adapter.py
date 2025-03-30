"""
AutoGen Framework Adapter

This module provides an adapter for using AutoGen agents within the Agent Management Server.
It handles initialization, execution, and management of AutoGen agents.
"""

import logging
from typing import Any, Dict, List, Optional
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient

from ..registry.models import AgentMetadata, AgentStatus, AgentCapability
from .base import FrameworkAdapter
from ..communication.chat_context import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

class AutoGenAdapter(FrameworkAdapter):
    """
    Adapter for AutoGen framework.
    
    This adapter allows the Agent Management Server to interact with AutoGen agents,
    providing standardized interfaces for initialization, execution, and status management.
    """
    
    async def initialize_agent(self, metadata: AgentMetadata) -> AssistantAgent:
        """
        Initialize an AutoGen agent from metadata.
        
        Args:
            metadata: Agent metadata containing configuration
            
        Returns:
            Initialized AutoGen AssistantAgent
            
        Raises:
            Exception: If initialization fails
        """
        logger.info(f"Initializing AutoGen agent: {metadata.name}")
        
        try:
            # Extract configuration from metadata
            agent_config = metadata.config or {}
            
            # Get the LLM configuration
            llm_config = agent_config.get("llm_config", {})
            
            # Ensure we have an API key if one isn't provided
            api_key = None
            if "api_key" in llm_config:
                api_key = llm_config["api_key"]
            else:
                # Get API key from environment
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("OPENAI_API_KEY not found in environment variables")
            
            model_name = llm_config.get("model", "gpt-4o")
            logger.debug(f"Creating AutoGen agent with model: {model_name}")
            
            # Initialize AssistantAgent
            agent = AssistantAgent(
                name=metadata.name,
                system_message=metadata.system_prompt,
                model_client=OpenAIChatCompletionClient(
                    model=model_name,
                    api_key=api_key
                ),
            )
            
            logger.info(f"Successfully initialized AutoGen agent: {metadata.name}")
            return agent
        except Exception as e:
            logger.error(f"Failed to initialize AutoGen agent: {str(e)}")
            raise
    
    async def execute_agent(self, agent: AssistantAgent, task: str, messages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute a task using the AutoGen agent.
        
        Args:
            agent: The AutoGen agent to execute
            task: The task description
            messages: Optional list of previous messages for context
            
        Returns:
            Dictionary containing execution results
            
        Raises:
            Exception: If execution fails
        """
        logger.info(f"Executing task with AutoGen agent '{agent.name}': {task[:100]}...")
        
        try:
            # Prepare history from messages if available
            history = ""
            if messages and len(messages) > 0:
                logger.debug(f"Processing {len(messages)} previous messages for context")
                
                # Skip processing if no substantive messages
                has_substantive_messages = any(
                    msg.get("sender_id") != "system" and 
                    msg.get("content", "").strip() != "" 
                    for msg in messages
                )
                
                if has_substantive_messages:
                    # Create a temporary ChatSession to format the history
                    temp_session = ChatSession("temp", {"agents": []})
                    message_count = 0
                    
                    for msg in messages:
                        if msg.get("sender_id") == "system" or not msg.get("content", "").strip():
                            continue
                        
                        try:
                            temp_msg = ChatMessage(
                                content=msg.get("content", ""),
                                sender_id=msg.get("sender_id", "unknown"),
                                sender_name=msg.get("sender_name", msg.get("sender_id", "unknown")),
                                metadata=msg.get("metadata", {})
                            )
                            temp_session.add_message(temp_msg)
                            message_count += 1
                        except Exception as msg_e:
                            logger.warning(f"Error processing message for history: {str(msg_e)}")
                    
                    logger.debug(f"Added {message_count} messages to temporary session for formatting")
                    
                    # Get formatted history 
                    history = temp_session.get_formatted_history(include_framework=True)
            
            # Prepare the final task description with history
            final_task = task
            if history:
                logger.debug("Adding message history to task description")
                final_task = (
                    f"{task}\n\n"
                    f"### PREVIOUS CONTRIBUTIONS FROM OTHER AGENTS ###\n\n"
                    f"{history}\n\n"
                    f"IMPORTANT: Consider the above previous contributions when responding to this task. "
                    f"Your response should build upon the work already done by other agents."
                )
            
            # Execute using autogen_agentchat
            logger.debug(f"Sending message to AutoGen agent '{agent.name}'")
            cancellation_token = CancellationToken()
            chat_response = await agent.on_messages(
                [TextMessage(content=final_task, source="user")],
                cancellation_token=cancellation_token,
            )
            response_content = chat_response.chat_message.content
            logger.info(f"Received response from AutoGen agent '{agent.name}'")
            
            # Process and return the response
            return {
                "agent_name": agent.name,
                "task": task,
                "response": response_content,
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Error executing task with AutoGen agent '{agent.name}': {str(e)}")
            return {
                "agent_name": agent.name,
                "task": task,
                "error": str(e),
                "response": f"Error executing AutoGen agent: {str(e)}",
                "status": "error"
            }
    
    async def get_agent_status(self, agent: AssistantAgent) -> AgentStatus:
        """
        Get the status of an AutoGen agent.
        
        Args:
            agent: The AutoGen agent
            
        Returns:
            The agent status
        """
        try:
            # AutoGen agents are always considered ready
            return AgentStatus.READY
        except Exception as e:
            logger.error(f"Error getting status for AutoGen agent '{agent.name}': {str(e)}")
            return AgentStatus.ERROR
    
    async def terminate_agent(self, agent: AssistantAgent) -> bool:
        """
        Terminate the AutoGen agent.
        
        Args:
            agent: The AutoGen agent to terminate
            
        Returns:
            True if termination is successful
        """
        try:
            # Reset the agent state if possible
            if hasattr(agent, "reset"):
                agent.reset()
                
            logger.info(f"Terminated AutoGen agent: {agent.name}")
            return True
        except Exception as e:
            logger.error(f"Error terminating AutoGen agent '{agent.name}': {str(e)}")
            return False
    
    async def get_agent_capabilities(self, agent: AssistantAgent) -> Dict[str, Any]:
        """
        Get the capabilities of the AutoGen agent.
        
        Args:
            agent: The AutoGen agent
            
        Returns:
            Dictionary containing agent capabilities
        """
        try:
            capabilities = [
                AgentCapability(
                    name="text_generation",
                    description="Can generate text responses based on prompts"
                )
            ]
            
            # Check for function calling capability
            if hasattr(agent, "_llm_config") and agent._llm_config.get("functions"):
                capabilities.append(AgentCapability(
                    name="function_calling",
                    description="Can call predefined functions"
                ))
            
            logger.debug(f"Retrieved capabilities for AutoGen agent: {agent.name}")
            
            return {
                "capabilities": capabilities,
                "agent_type": type(agent).__name__
            }
        except Exception as e:
            logger.error(f"Error getting capabilities for AutoGen agent '{agent.name}': {str(e)}")
            return {
                "capabilities": [],
                "agent_type": "AutoGen Agent",
                "error": str(e)
            } 