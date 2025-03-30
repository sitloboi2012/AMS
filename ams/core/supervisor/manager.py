import logging
import json
from typing import Dict, List, Any, Optional
import openai

from ..registry.base import AgentRegistry
from ..registry.models import AgentMetadata
from ..registry.capability_registry import capability_registry
from ..communication.hub import CommunicationHub
from .base import SupervisorAgent

logger = logging.getLogger(__name__)

class SupervisorManager(SupervisorAgent):
    """
    Manager agent that coordinates agent selection and collaboration.
    Inspired by K8s Control Plane architecture.
    """
    
    def __init__(
        self, 
        agent_registry: AgentRegistry, 
        communication_hub: CommunicationHub,
        llm_config: Optional[Dict[str, Any]] = None
    ):
        self.agent_registry = agent_registry
        self.communication_hub = communication_hub
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        self.llm_config = llm_config or {
            "model": "gpt-4o",
            "temperature": 0.1
        }
        
        # Configure the capability registry with the same LLM config
        capability_registry.llm_config = self.llm_config
    
    async def analyze_task(self, task: str) -> Dict[str, Any]:
        """
        Analyze the task using an LLM to determine required capabilities.
        
        Args:
            task: The task description
            
        Returns:
            Analysis results including required capabilities
        """
        logger.info(f"Analyzing task with LLM: {task}")
        
        # Use OpenAI API to analyze the task
        try:
            # First get a general task analysis with complexity and subtasks
            messages = [
                {"role": "system", "content": """You are a task analyzer that provides insights about a given task.
                Analyze the task and provide a detailed assessment.
                
                Return your analysis as a JSON object with the following format:
                {
                    "task_summary": "Brief summary of the task",
                    "complexity": 5,  // On a scale of 1-10
                    "subtasks": ["subtask1", "subtask2"],
                    "fields": ["field1", "field2"]  // Knowledge domains relevant to the task
                }
                """
                },
                {"role": "user", "content": f"Analyze this task: {task}"}
            ]
            
            response = openai.chat.completions.create(
                model=self.llm_config.get("model", "gpt-4o"),
                temperature=self.llm_config.get("temperature", 0.1),
                messages=messages
            )
            
            # Extract the JSON response
            content = response.choices[0].message.content
            try:
                task_analysis = json.loads(content)
            except json.JSONDecodeError:
                logger.warning(f"LLM response was not valid JSON: {content}")
                # Create a basic analysis if JSON parsing fails
                task_analysis = {
                    "task_summary": task,
                    "complexity": 5,
                    "subtasks": [task],
                    "fields": []
                }
            
            # Now use our capability registry to determine required capabilities
            capability_scores = await capability_registry.analyze_capabilities_with_llm(
                task, task_analysis
            )
            
            # Add required capabilities to the analysis
            required_capabilities = [
                name for name, score in capability_scores.items() 
                if score >= 0.5  # Use threshold of 0.5
            ]
            
            # If no capabilities were identified, default to text_generation
            if not required_capabilities:
                required_capabilities = ["text_generation"]
                logger.info("No specific capabilities identified. Defaulting to text_generation.")
            
            # Add the identified capabilities and scores to the analysis
            task_analysis["required_capabilities"] = required_capabilities
            task_analysis["capability_scores"] = capability_scores
            task_analysis["task"] = task
            
            logger.info(f"Task analysis complete with capabilities: {required_capabilities}")
            return task_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing task with LLM: {str(e)}")
            # Fallback to using the capability registry directly with minimal task analysis
            simple_analysis = {"task": task, "complexity": 5}
            
            try:
                capability_scores = await capability_registry.analyze_capabilities_with_llm(
                    task, simple_analysis
                )
                required_capabilities = [
                    name for name, score in capability_scores.items() 
                    if score >= 0.5
                ]
            except Exception as inner_e:
                logger.error(f"Error using capability registry: {str(inner_e)}")
                required_capabilities = ["text_generation"]
            
            # Ensure we have at least one capability
            if not required_capabilities:
                required_capabilities = ["text_generation"]
            
            return {
                "task": task,
                "task_summary": task,
                "complexity": 5,
                "required_capabilities": required_capabilities,
                "reasoning": "Fallback analysis using capability registry due to LLM error"
            }
    
    async def select_agents(self, task_analysis: Dict[str, Any]) -> List[AgentMetadata]:
        """
        Select appropriate agents based on task analysis.
        
        Args:
            task_analysis: The task analysis results
            
        Returns:
            List of selected agents
        """
        logger.info(f"Selecting agents for task: {task_analysis['task']}")
        
        # Get the original task
        task = task_analysis.get("task", "")
        
        # Get all registered agents
        all_agents = await self.agent_registry.list_agents()
        
        # Use the capability registry to filter agents based on the task
        selected_agents = await capability_registry.filter_agents_by_capabilities(
            agents=all_agents,
            task=task,
            task_analysis=task_analysis,
            threshold=0.5
        )
        
        logger.info(f"Selected {len(selected_agents)} agents for the task")
        return selected_agents
    
    async def create_collaboration(
        self, 
        agents: List[AgentMetadata], 
        task: str
    ) -> str:
        """
        Create a new collaboration session with selected agents.
        
        Args:
            agents: List of selected agents
            task: The task description
            
        Returns:
            The session ID
        """
        logger.info(f"Creating collaboration for task: {task}")
        
        # Create a new session in the communication hub
        session_id = self.communication_hub.create_session(task, agents)
        
        # Store session info
        self.active_sessions[session_id] = {
            "task": task,
            "agents": [agent.id for agent in agents],
            "status": "active"
        }
        
        # Add a system message to initiate the collaboration
        self.communication_hub.send_message(
            session_id=session_id,
            content=f"Task: {task}\n\nPlease collaborate to complete this task.",
            sender_id="system",
            sender_name="Supervisor",
            metadata={"type": "system", "task": task}
        )
        
        logger.info(f"Created collaboration session {session_id}")
        return session_id
    
    async def monitor_collaboration(self, session_id: str) -> Dict[str, Any]:
        """
        Monitor the status and progress of a collaboration session.
        
        Args:
            session_id: The session ID
            
        Returns:
            Session status information
            
        Raises:
            ValueError: If the session doesn't exist
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # Get the message history from the communication hub
        messages = self.communication_hub.get_session_history(session_id)
        
        status = {
            "session_id": session_id,
            "status": self.active_sessions[session_id]["status"],
            "message_count": len(messages),
            "last_update": messages[-1]["timestamp"] if messages else None,
        }
        
        logger.info(f"Monitored session {session_id}: {status['status']}")
        return status
    
    async def terminate_collaboration(self, session_id: str) -> bool:
        """
        Terminate a collaboration session.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if the session was terminated successfully
            
        Raises:
            ValueError: If the session doesn't exist
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # Add a system message indicating termination
        self.communication_hub.send_message(
            session_id=session_id,
            content="This collaboration session has been terminated by the supervisor.",
            sender_id="system",
            sender_name="Supervisor",
            metadata={"type": "system", "action": "terminate"}
        )
        
        # Terminate the session in the communication hub
        self.communication_hub.terminate_session(session_id)
        
        # Update session info
        self.active_sessions[session_id]["status"] = "terminated"
        
        logger.info(f"Terminated collaboration session {session_id}")
        return True
        
    async def determine_agent_execution_order(self, agents: List[AgentMetadata]) -> List[AgentMetadata]:
        """
        Determine the optimal execution order for agents in a collaboration.
        
        This method uses agent metadata, roles, and dependencies to create
        an optimal execution sequence for a multi-agent collaboration task.
        
        Args:
            agents: List of agent metadata objects
            
        Returns:
            Ordered list of agents optimized for collaboration efficiency
        """
        logger.info(f"Determining optimal execution order for {len(agents)} agents")
        
        # Define the execution priority for different agent roles
        role_priorities = {
            "research": 1,
            "strategist": 2, 
            "writer": 3,
            "content": 3,  # Same priority as writer
            "evaluator": 4,
            "reviewer": 4   # Same priority as evaluator
        }
        
        # Default priority for agents that don't match any category
        default_priority = 5
        
        # Build a dependency graph
        dependencies = {}  # agent_id -> list of agent_ids it depends on
        agent_map = {agent.id: agent for agent in agents}
        
        # First pass: collect explicit dependencies from agent configs
        for agent in agents:
            if agent.config and "depends_on" in agent.config:
                depends_on = agent.config["depends_on"]
                if isinstance(depends_on, list):
                    # Filter to only include valid agent IDs
                    valid_dependencies = [dep for dep in depends_on if dep in agent_map]
                    dependencies[agent.id] = valid_dependencies
                elif isinstance(depends_on, str) and depends_on in agent_map:
                    dependencies[agent.id] = [depends_on]
        
        # Assign priority to each agent based on various factors
        prioritized_agents = []
        for agent in agents:
            # Check if the agent has an explicitly defined execution priority in its config
            if agent.config and "execution_priority" in agent.config:
                try:
                    # Use the explicitly defined priority
                    agent_priority = int(agent.config["execution_priority"])
                    prioritized_agents.append((agent_priority, agent))
                    continue
                except (ValueError, TypeError):
                    logger.warning(f"Invalid execution_priority in agent config for {agent.name}")
            
            # Check agent name and description for role indicators
            agent_priority = default_priority
            agent_text = f"{agent.name.lower()} {agent.description.lower()}"
            
            # Find the highest priority role that matches this agent
            for role, priority in role_priorities.items():
                if role in agent_text:
                    agent_priority = min(agent_priority, priority)  # Use the highest priority (lowest number)
            
            # Check capabilities if available
            if agent.capabilities:
                for capability in agent.capabilities:
                    # Look for capabilities that might indicate a role
                    capability_name = capability.name.lower()
                    if "research" in capability_name and role_priorities.get("research", 99) < agent_priority:
                        agent_priority = role_priorities["research"]
                    elif "strategy" in capability_name and role_priorities.get("strategist", 99) < agent_priority:
                        agent_priority = role_priorities["strategist"]
                    elif "content" in capability_name and role_priorities.get("content", 99) < agent_priority:
                        agent_priority = role_priorities["content"]
                    elif "evaluate" in capability_name and role_priorities.get("evaluator", 99) < agent_priority:
                        agent_priority = role_priorities["evaluator"]
                    # Check if the capability has execution_order info
                    elif capability.parameters and "execution_priority" in capability.parameters:
                        try:
                            priority = int(capability.parameters["execution_priority"])
                            agent_priority = min(agent_priority, priority)
                        except (ValueError, TypeError):
                            pass
            
            # Store the agent with its priority
            prioritized_agents.append((agent_priority, agent))
        
        # Sort agents by priority
        prioritized_agents.sort(key=lambda x: x[0])
        sorted_agents = [agent for _, agent in prioritized_agents]
        
        # Process dependencies to ensure proper execution order
        if dependencies:
            # Create a final execution order respecting dependencies
            processed = set()
            agent_execution_order = []
            
            def add_with_dependencies(agent_id):
                """Add an agent and its dependencies to the execution order."""
                if agent_id in processed:
                    return
                
                # First add dependencies
                if agent_id in dependencies:
                    for dep_id in dependencies[agent_id]:
                        add_with_dependencies(dep_id)
                
                # Then add the agent if it hasn't been processed
                if agent_id not in processed and agent_id in agent_map:
                    agent_execution_order.append(agent_map[agent_id])
                    processed.add(agent_id)
            
            # Process each agent in priority order
            for agent in sorted_agents:
                add_with_dependencies(agent.id)
            
            # Add any remaining agents that weren't processed
            for agent in sorted_agents:
                if agent.id not in processed:
                    agent_execution_order.append(agent)
                    processed.add(agent.id)
        else:
            # If no dependencies, just use the priority-sorted list
            agent_execution_order = sorted_agents
        
        # If no order was determined, use the original order
        if not agent_execution_order:
            agent_execution_order = agents
        
        logger.info(f"Determined execution order: {[agent.name for agent in agent_execution_order]}")
        return agent_execution_order 