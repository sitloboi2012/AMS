"""
API Application

This module defines the FastAPI application and all its routes.
"""

import logging
import uuid
from typing import Dict, List, Any, Union
from dataclasses import asdict

from fastapi import FastAPI, Path, Request
from fastapi.middleware.cors import CORSMiddleware

from ..core.registry import InMemoryAgentRegistry, AgentMetadata, AgentFramework, AgentStatus, AgentCapability
from ..core.adapters import get_adapter
from ..core.supervisor import SupervisorManager
from ..core.communication import CommunicationHub
from ..core.errors import (
    AgentNotFoundException,
    SessionNotFoundException,
    InvalidAgentDataException,
    NoSuitableAgentsException
)

from .middleware import setup_middleware
from .models import (
    AgentCapabilityModel,
    AgentRegistrationRequest,
    AgentResponse,
    TaskRequest,
    TaskResponse,
    MessageRequest,
)

# Set up logging
logger = logging.getLogger(__name__)

# Create application dependencies
agent_registry = InMemoryAgentRegistry()
communication_hub = CommunicationHub()
supervisor = SupervisorManager(agent_registry, communication_hub)

# Helper function to convert between different agent capability models
def convert_capability(cap: Union[AgentCapabilityModel, Dict[str, Any]]) -> AgentCapability:
    """
    Converts a dataclass AgentCapabilityModel or dictionary to a core AgentCapability object.
    
    Args:
        cap: The capability model to convert (dataclass or dict)
        
    Returns:
        An AgentCapability object with the same attributes
    """
    # If cap is a dictionary, access items with dictionary notation
    if isinstance(cap, dict):
        return AgentCapability(
            name=cap["name"],
            description=cap["description"],
            parameters=cap.get("parameters")
        )
    # Otherwise, if it's a dataclass, use attribute notation
    else:
        return AgentCapability(
            name=cap.name,
            description=cap.description,
            parameters=cap.parameters
        )

# Helper function for JSON parsing
async def parse_json_request(request: Request) -> dict:
    """
    Parse a JSON request body.
    
    Args:
        request: The request object
        
    Returns:
        The parsed JSON data
    """
    return await request.json()

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        A configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="Agent Management Server (AMS)",
        description="A server for managing and orchestrating AI agents from different frameworks.",
        version="0.1.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For development; restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Set up custom middleware
    setup_middleware(app)
    
    # Include API routes
    @app.get("/")
    async def root() -> Dict[str, str]:
        """
        Root endpoint that returns a welcome message.
        
        Returns:
            A dictionary with a welcome message
        """
        return {"message": "Welcome to the Agent Management Server (AMS)"}
    
    # Register other routes
    @app.post("/agents", response_model=dict)
    async def register_agent(request: Request) -> Dict[str, Any]:
        """
        Register a new agent with the system.
        
        Args:
            request: The HTTP request containing agent data
            
        Returns:
            The registered agent's information
        """
        try:
            # Parse request body
            json_data = await parse_json_request(request)
            
            # Convert to dataclass
            agent_data = AgentRegistrationRequest(**json_data)
            
            # Convert framework string to enum
            try:
                framework = AgentFramework(agent_data.framework.lower())
            except ValueError:
                raise InvalidAgentDataException(
                    f"Invalid framework: {agent_data.framework}. Supported frameworks: {[f.value for f in AgentFramework]}",
                    details={"supported_frameworks": [f.value for f in AgentFramework]}
                )
            
            # Convert capabilities
            capabilities = None
            if agent_data.capabilities:
                capabilities = [convert_capability(cap) for cap in agent_data.capabilities]
            
            # Create agent metadata
            agent = AgentMetadata(
                id=str(uuid.uuid4()),
                name=agent_data.name,
                description=agent_data.description,
                system_prompt=agent_data.system_prompt,
                framework=framework,
                capabilities=capabilities,
                config=agent_data.config,
                status=AgentStatus.READY  # Set status to READY by default
            )
            
            # Register the agent
            agent_id = await agent_registry.register_agent(agent)
            
            # Get the registered agent
            registered_agent = await agent_registry.get_agent(agent_id)
            
            # Convert to response model
            response = AgentResponse(
                id=registered_agent.id,
                name=registered_agent.name,
                description=registered_agent.description,
                framework=registered_agent.framework.value,
                status=registered_agent.status.value,
                created_at=registered_agent.created_at,
                updated_at=registered_agent.updated_at
            )
            
            return asdict(response)
        except Exception as e:
            logger.error(f"Error registering agent: {str(e)}")
            raise
            
    @app.get("/agents", response_model=List[dict])
    async def list_agents() -> List[Dict[str, Any]]:
        """
        List all registered agents.
        
        Returns:
            A list of all registered agents
            
        Raises:
            HTTPException: If there's an error retrieving the agents
        """
        try:
            agents = await agent_registry.list_agents()
            
            return [
                asdict(AgentResponse(
                    id=agent.id,
                    name=agent.name,
                    description=agent.description,
                    framework=agent.framework.value,
                    status=agent.status.value,
                    created_at=agent.created_at,
                    updated_at=agent.updated_at
                ))
                for agent in agents
            ]
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            raise
    
    @app.get("/agents/{agent_id}", response_model=dict)
    async def get_agent(agent_id: str = Path(..., description="The ID of the agent to retrieve")) -> Dict[str, Any]:
        """
        Get details of a specific agent.
        
        Args:
            agent_id: The ID of the agent to retrieve
            
        Returns:
            The agent's information
            
        Raises:
            HTTPException: If the agent is not found or there's an error retrieving it
        """
        try:
            agent = await agent_registry.get_agent(agent_id)
            
            if not agent:
                raise AgentNotFoundException(agent_id)
            
            response = AgentResponse(
                id=agent.id,
                name=agent.name,
                description=agent.description,
                framework=agent.framework.value,
                status=agent.status.value,
                created_at=agent.created_at,
                updated_at=agent.updated_at
            )
            
            return asdict(response)
        except AgentNotFoundException as e:
            logger.error(f"Agent not found: {agent_id}")
            raise
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {str(e)}")
            raise

    @app.delete("/agents/{agent_id}", response_model=Dict[str, str])
    async def delete_agent(agent_id: str) -> Dict[str, str]:
        """Delete an agent from the registry."""
        try:
            deleted = await agent_registry.delete_agent(agent_id)
            
            if not deleted:
                raise AgentNotFoundException(agent_id)
            
            return {"message": f"Agent {agent_id} deleted successfully"}
        except AgentNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting agent {agent_id}: {str(e)}")
            raise

    # Task Execution Endpoints
    @app.post("/tasks", response_model=dict)
    async def create_task(request: Request) -> Dict[str, Any]:
        """Create a new task and assign appropriate agents."""
        try:
            # Parse request body
            json_data = await parse_json_request(request)
            
            # Convert to dataclass
            task_request = TaskRequest(**json_data)
            
            # Analyze the task
            task_analysis = await supervisor.analyze_task(task_request.task)
            
            # Select agents based on task analysis
            selected_agents = await supervisor.select_agents(task_analysis)
            
            if not selected_agents:
                raise NoSuitableAgentsException(
                    task_request.task, 
                    details={"message": "No suitable agents found for this task. Please register appropriate agents first."}
                )
            
            # Create a collaboration session
            session_id = await supervisor.create_collaboration(selected_agents, task_request.task)
            
            response = TaskResponse(
                session_id=session_id,
                task=task_request.task,
                agents=[agent.id for agent in selected_agents],
                status="created"
            )
            
            return asdict(response)
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise

    @app.post("/tasks/{session_id}/execute", response_model=Dict[str, Any])
    async def execute_task(session_id: str) -> Dict[str, Any]:
        """Execute a task with the selected agents."""
        try:
            # Get the session from the supervisor
            if session_id not in supervisor.active_sessions:
                raise SessionNotFoundException(session_id)
            
            session_info = supervisor.active_sessions[session_id]
            task = session_info["task"]
            agent_ids = session_info["agents"]
            
            # Get the session messages for context
            messages = communication_hub.get_session_history(session_id)
            
            # Get the formatted conversation history
            formatted_history = communication_hub.get_formatted_history(session_id, include_framework=True)
            
            # Get the agents from the registry
            agents = []
            for agent_id in agent_ids:
                agent = await agent_registry.get_agent(agent_id)
                if not agent:
                    raise AgentNotFoundException(agent_id)
                agents.append(agent)
            
            # Determine the optimal execution order using the supervisor
            agent_execution_order = await supervisor.determine_agent_execution_order(agents)
            
            # Log the execution order
            logger.info(f"Agent execution order: {[agent.name for agent in agent_execution_order]}")
            
            results = []
            for agent_metadata in agent_execution_order:
                try:
                    # Get the appropriate adapter for this agent's framework
                    adapter = get_adapter(agent_metadata.framework)
                    
                    # Initialize the agent
                    initialized_agent = await adapter.initialize_agent(agent_metadata)
                    
                    # Execute the agent with message history for context
                    execution_result = await adapter.execute_agent(initialized_agent, task, messages)
                    
                    # Add result to the list
                    results.append(execution_result)
                    
                    # Extract the appropriate content based on response structure
                    message_content = ""
                    if "response" in execution_result:
                        # AutoGen typically uses "response" field
                        message_content = execution_result["response"]
                    elif "result" in execution_result:
                        # CrewAI typically uses "result" field
                        message_content = execution_result["result"]
                    else:
                        # Fallback to string representation
                        message_content = str(execution_result)
                    
                    # Send the message with framework information
                    communication_hub.send_message(
                        session_id=session_id,
                        content=message_content,
                        sender_id=agent_metadata.id,
                        sender_name=agent_metadata.name,
                        metadata={
                            "type": "agent_response", 
                            "status": execution_result.get("status", "unknown"),
                            "framework": agent_metadata.framework.value
                        }
                    )
                    
                    # Get fresh formatted history for the next agent
                    messages = communication_hub.get_session_history(session_id)
                    formatted_history = communication_hub.get_formatted_history(session_id, include_framework=True)
                except Exception as e:
                    logger.error(f"Error executing agent {agent_metadata.id}: {str(e)}")
                    # Add the error to the session as a message
                    communication_hub.send_message(
                        session_id=session_id,
                        content=f"Error executing agent: {str(e)}",
                        sender_id=agent_metadata.id,
                        sender_name=agent_metadata.name,
                        metadata={"type": "error", "error": str(e), "framework": agent_metadata.framework.value}
                    )
            
            # Update session status
            supervisor.active_sessions[session_id]["status"] = "executed"
            
            return {
                "session_id": session_id,
                "task": task,
                "results": results,
                "status": "executed"
            }
        except SessionNotFoundException:
            raise
        except AgentNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            raise

    @app.get("/tasks/{session_id}", response_model=Dict[str, Any])
    async def get_task_status(session_id: str) -> Dict[str, Any]:
        """Get the status of a task."""
        try:
            status = await supervisor.monitor_collaboration(session_id)
            return status
        except SessionNotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error getting task status for session {session_id}: {str(e)}")
            raise

    @app.post("/tasks/{session_id}/messages", response_model=Dict[str, Any])
    async def send_message(session_id: str, request: Request) -> Dict[str, Any]:
        """Send a message to a collaboration session."""
        try:
            # Parse request body
            json_data = await parse_json_request(request)
            
            # Convert to dataclass
            message_request = MessageRequest(**json_data)
            
            message = communication_hub.send_message(
                session_id=session_id,
                content=message_request.content,
                sender_id=message_request.sender_id,
                sender_name=message_request.sender_name,
                metadata=message_request.metadata
            )
            
            return message.to_dict()
        except SessionNotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error sending message to session {session_id}: {str(e)}")
            raise

    @app.get("/tasks/{session_id}/messages", response_model=List[Dict[str, Any]])
    async def get_messages(session_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a collaboration session."""
        try:
            messages = communication_hub.get_session_history(session_id)
            return messages
        except SessionNotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {str(e)}")
            raise

    @app.post("/tasks/{session_id}/terminate", response_model=Dict[str, str])
    async def terminate_task(session_id: str) -> Dict[str, str]:
        """Terminate a task."""
        try:
            terminated = await supervisor.terminate_collaboration(session_id)
            return {"message": f"Task {session_id} terminated successfully"}
        except SessionNotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error terminating task {session_id}: {str(e)}")
            raise

    @app.post("/tasks/run", response_model=Dict[str, Any])
    async def create_and_execute_task(request: Request) -> Dict[str, Any]:
        """Create and execute a task in one call."""
        try:
            # Parse request body
            json_data = await parse_json_request(request)
            
            # Convert to dataclass
            task_request = TaskRequest(**json_data)
            
            # First create the task
            create_response = await create_task(request)
            session_id = create_response.get("session_id")
            
            # Then execute it
            execute_response = await execute_task(session_id)
            
            # Return combined response
            return {
                "creation": create_response,
                "execution": execute_response
            }
        except Exception as e:
            logger.error(f"Error creating and executing task: {str(e)}")
            raise
    
    return app 