# Framework Adapters

Framework adapters are a core component of the Agent Management Server (AMS) that enable it to work with multiple agent frameworks. This document explains how framework adapters work and how to implement them for new frameworks.

## Overview

Framework adapters serve as translation layers between AMS and specific agent frameworks. They abstract away the details of each framework's implementation, providing a consistent interface for the AMS to work with. This allows agents from different frameworks to collaborate seamlessly within the AMS ecosystem.

## Supported Frameworks

AMS currently includes adapters for the following frameworks:

1. **AutoGen**: Microsoft's multi-agent conversation framework
2. **CrewAI**: Framework for orchestrating role-playing agents

## Adapter Interface

All framework adapters implement the `FrameworkAdapter` interface, which defines the following key methods:

```python
class FrameworkAdapter(ABC):
    @abstractmethod
    async def initialize_agent(self, metadata: AgentMetadata) -> Any:
        """Initialize an agent using the specific framework."""
        pass

    @abstractmethod
    async def execute_agent(self, agent: Any, task: str, messages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Execute a task using the specific framework agent."""
        pass

    @abstractmethod
    async def get_agent_status(self, agent: Any) -> AgentStatus:
        """Get the status of the agent."""
        pass

    @abstractmethod
    async def terminate_agent(self, agent: Any) -> bool:
        """Terminate the agent."""
        pass

    @abstractmethod
    async def get_agent_capabilities(self, agent: Any) -> Dict[str, Any]:
        """Get the capabilities of the agent."""
        pass
```

## How Adapters Work

### 1. Initialization

When a new agent is registered with AMS:

1. The agent's framework is identified (e.g., "autogen", "crewai")
2. The appropriate adapter is selected based on the framework
3. The adapter's `initialize_agent` method is called with the agent's metadata
4. The adapter creates and initializes a framework-specific agent instance

### 2. Execution

When a task is assigned to an agent:

1. The adapter's `execute_agent` method is called with:
   - The agent instance
   - The task description
   - Any previous messages from the collaboration session
2. The adapter translates and formats the inputs for the specific framework
3. The agent processes the task using the framework's native execution mechanisms
4. The result is formatted in a standardized way and returned to AMS

### 3. Message Handling

The adapter handles translating between the internal message formats of the framework and the standardized message format used by AMS.

## AutoGen Adapter

The AutoGen adapter integrates with Microsoft's AutoGen framework. It handles:

1. **Agent Initialization**: Creates configured AutoGen user proxies or assistants
2. **Message Translation**: Translates between AutoGen's message formats and AMS formats
3. **Capability Detection**: Maps AutoGen agent types to AMS capabilities
4. **Execution Management**: Handles AutoGen's termination and status monitoring

Key implementation details:

```python
class AutoGenAdapter(FrameworkAdapter):
    async def initialize_agent(self, metadata: AgentMetadata) -> Any:
        # Extract config options from metadata
        config = metadata.config or {}
        llm_config = config.get("llm_config", {})
        
        # Create appropriate AutoGen agent type based on capabilities
        if self._has_capability(metadata, "code_execution"):
            # Create agent with code execution capability
            return autogen.AssistantAgent(
                name=metadata.name,
                system_message=metadata.system_prompt,
                llm_config=llm_config
            )
        else:
            # Create standard assistant agent
            return autogen.AssistantAgent(
                name=metadata.name,
                system_message=metadata.system_prompt,
                llm_config=llm_config
            )
```

## CrewAI Adapter

The CrewAI adapter integrates with the CrewAI framework for role-playing agents. It handles:

1. **Role Configuration**: Sets up CrewAI-specific role, goal, and backstory attributes
2. **Agent Creation**: Creates CrewAI agent instances with appropriate tools and settings
3. **Task Execution**: Handles CrewAI's task execution model
4. **Message Formatting**: Translates CrewAI outputs into standardized messages

Key implementation details:

```python
class CrewAIAdapter(FrameworkAdapter):
    async def initialize_agent(self, metadata: AgentMetadata) -> Any:
        # Extract CrewAI-specific configuration
        config = metadata.config or {}
        role = config.get("role", metadata.name)
        goal = config.get("goal", "Provide the best assistance possible.")
        backstory = config.get("backstory", "An AI assistant with specialized knowledge.")
        
        # Create a CrewAI agent
        return crew.Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            llm=self._create_llm(config.get("llm_config", {}))
        )
```

## Implementing a New Adapter

To add support for a new agent framework to AMS, follow these steps:

### 1. Create a New Adapter Class

Create a new file in the `ams/core/adapters` directory:

```python
# ams/core/adapters/my_framework_adapter.py

from typing import Any, Dict, List, Optional
from ..registry.models import AgentMetadata, AgentStatus, AgentCapability
from .base import FrameworkAdapter

class MyFrameworkAdapter(FrameworkAdapter):
    """Adapter for the MyFramework agent framework."""
    
    async def initialize_agent(self, metadata: AgentMetadata) -> Any:
        """Initialize a MyFramework agent."""
        # Convert AMS agent metadata to MyFramework configuration
        # Return the initialized MyFramework agent
        
    async def execute_agent(self, agent: Any, task: str, messages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Execute a task using a MyFramework agent."""
        # Convert task and messages to MyFramework format
        # Execute the task using MyFramework
        # Return the result in a standardized format
        
    async def get_agent_status(self, agent: Any) -> AgentStatus:
        """Get the status of a MyFramework agent."""
        # Return the agent's status
        
    async def terminate_agent(self, agent: Any) -> bool:
        """Terminate a MyFramework agent."""
        # Clean up any resources and terminate the agent
        # Return True if successful, False otherwise
        
    async def get_agent_capabilities(self, agent: Any) -> Dict[str, Any]:
        """Get the capabilities of a MyFramework agent."""
        # Determine the agent's capabilities based on its MyFramework configuration
        # Return a dictionary of capabilities
```

### 2. Register the Adapter

Add your adapter to the adapter registry in `ams/core/adapters/__init__.py`:

```python
from .my_framework_adapter import MyFrameworkAdapter
from ..registry.models import AgentFramework

# Update the ADAPTER_REGISTRY dictionary
ADAPTER_REGISTRY: Dict[AgentFramework, Type[FrameworkAdapter]] = {
    AgentFramework.AUTOGEN: AutoGenAdapter,
    AgentFramework.CREWAI: CrewAIAdapter,
    AgentFramework.MYFRAMEWORK: MyFrameworkAdapter,  # Add your adapter here
}
```

### 3. Update the AgentFramework Enum

Add your framework to the `AgentFramework` enum in `ams/core/registry/models.py`:

```python
class AgentFramework(str, Enum):
    AUTOGEN = "autogen"
    CREWAI = "crewai"
    MYFRAMEWORK = "myframework"  # Add your framework here
```

### 4. Implement Framework-Specific Logic

In your adapter, implement the necessary logic to:

1. **Convert Between Formats**: Translate between AMS and MyFramework data formats
2. **Handle Execution**: Process tasks and generate responses
3. **Manage Lifecycle**: Initialize, monitor, and terminate agent instances
4. **Map Capabilities**: Map between MyFramework agent types and AMS capabilities

### 5. Test Your Adapter

Write tests to verify that your adapter correctly:

1. Initializes agents
2. Executes tasks
3. Translates messages
4. Handles errors
5. Interacts with agents from other frameworks

## Best Practices

1. **Error Handling**: Implement robust error handling to capture and translate framework-specific errors.
2. **Resource Management**: Ensure proper cleanup of resources when agents are terminated.
3. **Type Safety**: Use type hints and implement runtime type checking for framework-specific objects.
4. **Configuration Validation**: Validate framework-specific configuration options during initialization.
5. **Capability Mapping**: Carefully map framework capabilities to AMS capability concepts.
6. **Documentation**: Document framework-specific configuration options and limitations.

## Planned Adaptations

Future adapter implementations planned for AMS include:

1. **AG2**: Advanced AutoGen framework with improved workflow management
2. **LangGraph**: LangChain's directed graph agent orchestration framework
3. **LlamaIndex**: Document-grounded agent framework
4. **Custom Frameworks**: Support for custom, user-defined agent frameworks

## Conclusion

Framework adapters are key to AMS's ability to provide a unified interface for working with different agent frameworks. By implementing the adapter interface, any agent framework can be integrated with AMS, enabling cross-framework agent collaboration and standardized management. 