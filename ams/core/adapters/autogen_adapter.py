import logging
from typing import Any, Dict

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient

from ..registry.models import AgentMetadata, AgentStatus, AgentCapability
from .base import FrameworkAdapter

logger = logging.getLogger(__name__)

class AutoGenAdapter(FrameworkAdapter):
    """Adapter for AutoGen framework."""
    
    async def initialize_agent(self, metadata: AgentMetadata) -> AssistantAgent:
        """Initialize an AutoGen agent from metadata."""
        logger.info(f"Initializing AutoGen agent: {metadata.name}")
        
        try:
            # Extract configuration from metadata
            agent_config = metadata.config or {}
            
            # Get the LLM configuration
            llm_config = agent_config.get("llm_config", {})
            
            # Ensure we have an API key if one isn't provided
            if "api_key" not in llm_config:
                # In a real implementation, we would get this from environment variables
                # or a secrets manager. For now, we'll just use a placeholder.
                import os
                api_key = os.environ.get("OPENAI_API_KEY")
                if api_key:
                    llm_config["api_key"] = api_key
            
            # Initialize only AssistantAgent
            agent = AssistantAgent(
                name=metadata.name,
                system_message=metadata.system_prompt,
                model_client=OpenAIChatCompletionClient(
                    model=llm_config.get("model", "gpt-4o"),
                    api_key=llm_config.get("api_key")
                ),
            )
            
            return agent
        except Exception as e:
            logger.error(f"Failed to initialize AutoGen agent: {str(e)}")
            raise
    
    async def execute_agent(self, agent: AssistantAgent, task: str) -> Dict[str, Any]:
        """Execute a task using the AutoGen agent."""
        logger.info(f"Executing task with agent {agent.name}: {task}")
        
        try:
            # Initialize a conversation
            chat_response = await agent.on_messages(
                [TextMessage(content=task, source="user")],
                cancellation_token=CancellationToken(),
            )
            
            # Process and return the response
            return {
                "agent_name": agent.name,
                "task": task,
                "response": chat_response.chat_message.content,
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Error executing task with AutoGen agent: {str(e)}")
            return {
                "agent_name": agent.name,
                "task": task,
                "error": str(e),
                "status": "error"
            }
    
    async def get_agent_status(self, agent: AssistantAgent) -> AgentStatus:
        """Get the current status of the AutoGen agent."""
        if not agent:
            return AgentStatus.ERROR
        
        if hasattr(agent, "_llm_config") and agent._llm_config:
            return AgentStatus.READY
        else:
            return AgentStatus.OFFLINE
    
    async def terminate_agent(self, agent: AssistantAgent) -> bool:
        """Terminate the AutoGen agent."""
        if hasattr(agent, "reset"):
            agent.reset()
        return True
    
    async def get_agent_capabilities(self, agent: AssistantAgent) -> Dict[str, Any]:
        """Get the capabilities of the AutoGen agent."""
        capabilities = [
            AgentCapability(
                name="text_generation",
                description="Can generate text responses based on prompts"
            )
        ]
        
        if hasattr(agent, "_llm_config") and agent._llm_config.get("functions"):
            capabilities.append(AgentCapability(
                name="function_calling",
                description="Can call predefined functions"
            ))
        
        return {
            "capabilities": capabilities,
            "agent_type": type(agent).__name__
        } 