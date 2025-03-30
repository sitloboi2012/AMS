import logging
import uuid
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..core.registry import InMemoryAgentRegistry, AgentMetadata, AgentFramework, AgentStatus, AgentCapability
from ..core.adapters import get_adapter
from ..core.supervisor import SupervisorManager
from ..core.communication import CommunicationHub

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create application dependencies
agent_registry = InMemoryAgentRegistry()
communication_hub = CommunicationHub()
supervisor = SupervisorManager(agent_registry, communication_hub)

# Create FastAPI app
app = FastAPI(
    title="Agent Management Server (AMS)",
    description="A server for managing and orchestrating AI agents from different frameworks.",
    version="0.1.0",
)

# API Models
class AgentCapabilityModel(BaseModel):
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None

class AgentRegistrationRequest(BaseModel):
    name: str
    description: str
    system_prompt: str
    framework: str
    capabilities: Optional[List[AgentCapabilityModel]] = None
    config: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    framework: str
    status: str
    created_at: str
    updated_at: str

class TaskRequest(BaseModel):
    task: str

class TaskResponse(BaseModel):
    session_id: str
    task: str
    agents: List[str]
    status: str = "created"

class MessageRequest(BaseModel):
    content: str
    sender_id: str
    sender_name: str
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    message_id: str
    content: str
    sender_id: str
    sender_name: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

# Helper function to convert between different agent capability models
def convert_capability(cap: AgentCapabilityModel) -> AgentCapability:
    return AgentCapability(
        name=cap.name,
        description=cap.description,
        parameters=cap.parameters
    )

# API Endpoints
@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Welcome to the Agent Management Server (AMS)"}

# Agent Management Endpoints
@app.post("/agents", response_model=AgentResponse)
async def register_agent(agent_data: AgentRegistrationRequest):
    """Register a new agent with the system."""
    try:
        # Convert framework string to enum
        try:
            framework = AgentFramework(agent_data.framework.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid framework: {agent_data.framework}. Supported frameworks: {[f.value for f in AgentFramework]}"
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
        
        return {
            "id": registered_agent.id,
            "name": registered_agent.name,
            "description": registered_agent.description,
            "framework": registered_agent.framework.value,
            "status": registered_agent.status.value,
            "created_at": registered_agent.created_at,
            "updated_at": registered_agent.updated_at
        }
    except Exception as e:
        logger.error(f"Error registering agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents", response_model=List[AgentResponse])
async def list_agents():
    """List all registered agents."""
    try:
        agents = await agent_registry.list_agents()
        
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "framework": agent.framework.value,
                "status": agent.status.value,
                "created_at": agent.created_at,
                "updated_at": agent.updated_at
            }
            for agent in agents
        ]
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get details of a specific agent."""
    try:
        agent = await agent_registry.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "framework": agent.framework.value,
            "status": agent.status.value,
            "created_at": agent.created_at,
            "updated_at": agent.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent from the registry."""
    try:
        deleted = await agent_registry.delete_agent(agent_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {"message": f"Agent {agent_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Task Execution Endpoints
@app.post("/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskRequest):
    """Create a new task and assign appropriate agents."""
    try:
        # Analyze the task
        task_analysis = await supervisor.analyze_task(task_request.task)
        
        # Select agents based on task analysis
        selected_agents = await supervisor.select_agents(task_analysis)
        
        if not selected_agents:
            raise HTTPException(
                status_code=400, 
                detail="No suitable agents found for this task. Please register appropriate agents first."
            )
        
        # Create a collaboration session
        session_id = await supervisor.create_collaboration(selected_agents, task_request.task)
        
        return {
            "session_id": session_id,
            "task": task_request.task,
            "agents": [agent.id for agent in selected_agents],
            "status": "created"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks/{session_id}/execute")
async def execute_task(session_id: str):
    """Execute a task with the selected agents."""
    try:
        # Get the session from the supervisor
        if session_id not in supervisor.active_sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
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
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{session_id}")
async def get_task_status(session_id: str):
    """Get the status of a task."""
    try:
        status = await supervisor.monitor_collaboration(session_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting task status for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks/{session_id}/messages", response_model=MessageResponse)
async def send_message(session_id: str, message_request: MessageRequest):
    """Send a message to a collaboration session."""
    try:
        message = communication_hub.send_message(
            session_id=session_id,
            content=message_request.content,
            sender_id=message_request.sender_id,
            sender_name=message_request.sender_name,
            metadata=message_request.metadata
        )
        
        return message.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message to session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{session_id}/messages")
async def get_messages(session_id: str):
    """Get all messages in a collaboration session."""
    try:
        messages = communication_hub.get_session_history(session_id)
        return messages
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting messages for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks/{session_id}/terminate")
async def terminate_task(session_id: str):
    """Terminate a task."""
    try:
        terminated = await supervisor.terminate_collaboration(session_id)
        return {"message": f"Task {session_id} terminated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error terminating task {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks/run", response_model=Dict[str, Any])
async def create_and_execute_task(task_request: TaskRequest):
    """Create and execute a task in one call."""
    try:
        # First create the task
        create_response = await create_task(task_request)
        session_id = create_response.get("session_id")
        
        # Then execute it
        execute_response = await execute_task(session_id)
        
        # Return combined response
        return {
            "creation": create_response,
            "execution": execute_response
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating and executing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 