import logging
from typing import Any, Dict, List, Optional
import os

from crewai import Agent as CrewAgent # type: ignore
from crewai import Crew, Task
from langchain_openai import ChatOpenAI

from ..registry.models import AgentMetadata, AgentStatus, AgentCapability
from .base import FrameworkAdapter

logger = logging.getLogger(__name__)

class CrewAIAdapter(FrameworkAdapter):
    """Adapter for CrewAI framework."""
    
    async def initialize_agent(self, metadata: AgentMetadata) -> CrewAgent:
        """Initialize a CrewAI agent from metadata."""
        logger.info(f"Initializing CrewAI agent: {metadata.name}")
        
        try:
            # Extract configuration from metadata
            agent_config = metadata.config or {}
            
            # Set up the LLM
            llm_config = agent_config.get("llm_config", {})
            model_name = llm_config.get("model", "gpt-4o")
            temperature = llm_config.get("temperature", 0.7)
            
            # Get API key from environment if not provided
            api_key = llm_config.get("api_key") or os.environ.get("OPENAI_API_KEY")
            
            # Create the LLM
            llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=api_key,
                verbose=True
            )
            
            # Create a CrewAI Agent
            agent = CrewAgent(
                name=metadata.name,
                role=agent_config.get("role", "AI Assistant"),
                goal=agent_config.get("goal", "Help solve the task"),
                backstory=agent_config.get("backstory", metadata.description),
                verbose=agent_config.get("verbose", True),
                allow_delegation=agent_config.get("allow_delegation", True),
                llm=llm,
                tools=agent_config.get("tools", [])
            )
            
            # Store the system prompt as an attribute for reference
            # (CrewAI doesn't use system_prompt directly, but we keep it for consistency)
            setattr(agent, "_system_prompt", metadata.system_prompt)
            
            return agent
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI agent: {str(e)}")
            raise
    
    async def execute_agent(self, agent: CrewAgent, task_description: str) -> Dict[str, Any]:
        """Execute a task using the CrewAI agent."""
        logger.info(f"Executing task with agent {agent.name}: {task_description}")
        
        try:
            # Create a CrewAI Task
            task = Task(
                description=task_description,
                agent=agent,
                expected_output=f"Complete analysis of the task: {task_description}",
            )
            
            # For standalone agent execution, we create a single-agent Crew
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True
            )
            
            # Execute the task
            result = crew.kickoff()
            
            return {
                "agent_name": agent.name,
                "task": task_description,
                "result": result,
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Error executing task with CrewAI agent: {str(e)}")
            return {
                "agent_name": agent.name,
                "task": task_description,
                "error": str(e),
                "status": "error"
            }
    
    async def get_agent_status(self, agent: CrewAgent) -> AgentStatus:
        """Get the current status of the CrewAI agent."""
        # CrewAI doesn't have built-in status tracking, so we implement a basic check
        if not agent:
            return AgentStatus.ERROR
        
        # Simple check - if agent has llm, it's likely ready
        if hasattr(agent, "llm") and agent.llm:
            return AgentStatus.READY
        else:
            return AgentStatus.OFFLINE
    
    async def terminate_agent(self, agent: CrewAgent) -> bool:
        """Terminate the CrewAI agent."""
        # CrewAI doesn't require explicit termination
        # But we could clear any state if needed in the future
        return True
    
    async def get_agent_capabilities(self, agent: CrewAgent) -> Dict[str, Any]:
        """Get the capabilities of the CrewAI agent."""
        capabilities = []
        
        # Basic capabilities of all CrewAI agents
        capabilities.append(AgentCapability(
            name="text_generation",
            description="Can generate text responses based on prompts"
        ))
        
        # Check for tools
        if hasattr(agent, "tools") and agent.tools:
            capabilities.append(AgentCapability(
                name="tool_use",
                description="Can use tools to complete tasks",
                parameters={"tools": [tool.__class__.__name__ for tool in agent.tools]}
            ))
        
        # Check for delegation capability
        if hasattr(agent, "allow_delegation") and agent.allow_delegation:
            capabilities.append(AgentCapability(
                name="delegation",
                description="Can delegate subtasks to other agents"
            ))
        
        return {
            "capabilities": capabilities,
            "agent_type": "CrewAI Agent",
            "role": agent.role if hasattr(agent, "role") else None,
            "goal": agent.goal if hasattr(agent, "goal") else None
        } 