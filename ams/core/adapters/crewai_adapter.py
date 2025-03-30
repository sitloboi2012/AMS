"""
CrewAI Framework Adapter

This module provides an adapter for using CrewAI agents within the Agent Management Server.
It handles initialization, execution, and management of CrewAI agents.
"""

import logging
import os
from typing import Any, Dict, List, Union

from crewai import Agent, Crew, Task # type: ignore
from crewai.crew import CrewOutput # type: ignore
from langchain_openai import ChatOpenAI # type: ignore

from ..registry.models import AgentMetadata, AgentStatus, AgentCapability
from .base import FrameworkAdapter
from ..communication.chat_context import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

class CrewAIAdapter(FrameworkAdapter):
    """
    Adapter for CrewAI framework.
    
    This adapter allows the Agent Management Server to interact with CrewAI agents,
    providing standardized interfaces for initialization, execution, and status management.
    """
    
    async def initialize_agent(self, metadata: AgentMetadata) -> Any:
        """
        Initialize a CrewAI agent from metadata.
        
        Args:
            metadata: Agent metadata containing configuration
            
        Returns:
            Initialized CrewAI agent
            
        Raises:
            Exception: If initialization fails
        """
        logger.info(f"Initializing CrewAI agent: {metadata.name}")
        
        try:
            # Extract configuration from metadata
            agent_config = metadata.config or {}
            
            # Extract necessary information from metadata
            name = metadata.name
            description = metadata.description
            system_prompt = metadata.system_prompt
            
            # Get API key 
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not found in environment variables")
            
            # Get LLM configuration from config
            llm_config = agent_config.get("llm_config", {})
            
            # Configure the language model
            llm = ChatOpenAI(
                openai_api_key=api_key,
                model=llm_config.get("model", "gpt-4o"),
                temperature=llm_config.get("temperature", 0.7),
            )
            
            # Get CrewAI specific configs
            role = agent_config.get("role", name)
            goal = agent_config.get("goal", description)
            backstory = agent_config.get("backstory", system_prompt)
            
            logger.debug(f"Creating CrewAI agent with role: {role}, model: {llm_config.get('model', 'gpt-4o')}")
            
            # Create the agent
            agent = Agent(
                role=role,
                goal=goal,
                backstory=backstory,
                verbose=True,
                allow_delegation=False,
                tools=[],  # No tools for this example
                llm=llm,
            )
            
            logger.info(f"Successfully initialized CrewAI agent: {name}")
            return agent
        except Exception as e:
            logger.error(f"Error initializing CrewAI agent: {str(e)}")
            raise
    
    async def execute_agent(self, agent: Agent, task: str, messages: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task using the CrewAI agent.
        
        Args:
            agent: The CrewAI agent to execute
            task: The task description
            messages: Optional list of previous messages for context
            
        Returns:
            Dictionary containing execution results
            
        Raises:
            Exception: If execution fails
        """
        agent_name = getattr(agent, "role", "Unknown Agent")
        logger.info(f"Executing task with CrewAI agent '{agent_name}': {task[:100]}...")
        
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
            
            # Create a CrewAI Task
            logger.debug("Creating CrewAI task")
            crew_task = Task(
                description=final_task,
                agent=agent,
                expected_output="Comprehensive response to the task",
            )
            
            # Create a crew with just this agent
            crew = Crew(
                agents=[agent],
                tasks=[crew_task],
                verbose=True,
            )
            
            # Execute the task
            logger.info(f"Executing CrewAI task with agent '{agent_name}'")
            result = crew.kickoff()
            logger.info(f"CrewAI task execution completed for agent '{agent_name}'")
            
            # Process the result to extract plain text content
            result_content = self._extract_content(result)
            
            # Return the result
            return {
                "agent_name": agent.role,
                "task": task,
                "result": result_content,
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Error executing task with CrewAI agent '{agent_name}': {str(e)}")
            return {
                "agent_name": getattr(agent, "role", "Unknown"),
                "task": task,
                "error": str(e),
                "result": f"Error executing CrewAI agent: {str(e)}",
                "status": "error"
            }
    
    def _extract_content(self, result: Union[CrewOutput, str, Any]) -> str:
        """
        Extract content from the CrewAI result.
        
        Args:
            result: The result from CrewAI execution
            
        Returns:
            Extracted content as a string
        """
        try:
            logger.debug(f"Extracting content from CrewAI result of type: {type(result).__name__}")
            
            # Handle different result formats
            if hasattr(result, "raw"):
                # CrewAI typically returns an object with a 'raw' attribute
                return result.raw
            elif isinstance(result, str):
                # If it's already a string, return it directly
                return result
            else:
                # Try to convert to string
                return str(result)
        except Exception as e:
            logger.error(f"Error extracting content from CrewAI result: {str(e)}")
            return str(result)
    
    async def get_agent_status(self, agent: Any) -> AgentStatus:
        """
        Get the status of a CrewAI agent.
        
        Args:
            agent: The CrewAI agent
            
        Returns:
            The agent status
        """
        try:
            # CrewAI agents are always considered ready
            return AgentStatus.READY
        except Exception as e:
            logger.error(f"Error getting agent status: {str(e)}")
            return AgentStatus.ERROR
    
    async def terminate_agent(self, agent: Any) -> bool:
        """
        Terminate a CrewAI agent.
        
        Args:
            agent: The CrewAI agent to terminate
            
        Returns:
            True if termination is successful
        """
        try:
            # CrewAI agents don't need explicit termination
            logger.info(f"Terminated CrewAI agent: {getattr(agent, 'role', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Error terminating CrewAI agent: {str(e)}")
            return False
    
    async def get_agent_capabilities(self, agent: Any) -> Dict[str, Any]:
        """
        Get the capabilities of the CrewAI agent.
        
        Args:
            agent: The CrewAI agent
            
        Returns:
            Dictionary containing agent capabilities
        """
        try:
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
            
            # Get agent identifiers safely
            role = getattr(agent, "role", None)
            goal = getattr(agent, "goal", None)
            agent_name = getattr(agent, "_agent_name", role)
            
            logger.debug(f"Retrieved capabilities for CrewAI agent: {role or agent_name}")
            
            return {
                "capabilities": capabilities,
                "agent_type": "CrewAI Agent",
                "agent_name": agent_name,
                "role": role,
                "goal": goal
            }
        except Exception as e:
            logger.error(f"Error getting agent capabilities: {str(e)}")
            return {
                "capabilities": [],
                "agent_type": "CrewAI Agent",
                "error": str(e)
            } 