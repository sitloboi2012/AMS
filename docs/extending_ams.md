# Extending the Agent Management Server

This guide explains how to extend the Agent Management Server (AMS) to add new capabilities, integrate new agent frameworks, and customize the system for specific use cases.

## 1. Adding New Agent Capabilities

Agent capabilities define what an agent can do within the system. There are two main ways to add new capabilities:

### 1.1 Define the Capability for an Agent

Capabilities are defined in the `AgentCapability` class. They consist of:
- `name`: A unique identifier for the capability
- `description`: A human-readable description
- `parameters`: Optional parameters specific to that capability

Example of registering an agent with a custom capability:

```python
agent_data = {
    "name": "CustomAgent",
    "description": "An agent with custom capabilities",
    "system_prompt": "You are an agent with specialized capabilities.",
    "framework": "autogen",
    "capabilities": [
        {
            "name": "custom_analysis",
            "description": "Can perform specialized data analysis",
            "parameters": {
                "analysis_type": "financial",
                "data_format": "json"
            }
        }
    ],
    "config": {
        "llm_config": {
            "model": "gpt-4",
            "temperature": 0.7
        }
    }
}

# Register with the AMS API
response = requests.post("http://localhost:8000/agents", json=agent_data)
```

### 1.2 Register a Capability in the CapabilityRegistry

AMS uses a capability registry system to detect and match capabilities to tasks. You can register new capabilities in the registry to make the system recognize and utilize them:

```python
from ams.core.registry.capability_registry import capability_registry

# Register a new capability with description and example tasks
capability_registry.register_capability(
    capability_name="custom_analysis",
    description="Ability to perform specialized financial data analysis including trend detection, anomaly identification, and forecasting based on numerical data.",
    examples=[
        "Analyze these financial statements and identify trends",
        "Detect anomalies in this market data",
        "Create a forecast based on historical financial data"
    ]
)
```

The capability registry uses LLM-based semantic matching to determine which capabilities are needed for a task. This is more flexible than keyword matching as it understands the meaning and context of the task.

### 1.3 Implement Capability Detection in Framework Adapters

To support a new capability in a framework adapter, modify the `get_agent_capabilities` method:

```python
async def get_agent_capabilities(self, agent: Any) -> Dict[str, Any]:
    capabilities = [
        # Existing capabilities...
        
        # Check for custom capability
        AgentCapability(
            name="custom_analysis",
            description="Can perform specialized data analysis",
            parameters={
                "analysis_type": "financial",
                "data_format": "json"
            }
        )
    ]
    
    return {
        "capabilities": capabilities,
        "agent_type": "Custom Agent"
    }
```

### 1.4 Complete Capability Extension Example

Here's a complete example of extending the system with a new capability:

```python
# 1. Create a script to extend AMS with a new capability
from ams.core.registry.capability_registry import capability_registry
from ams.core.registry.models import AgentCapability

# 2. Register the capability with descriptive information
capability_registry.register_capability(
    capability_name="sentiment_analysis",
    description="Ability to analyze sentiment and emotions in text. Can detect positive, negative, and neutral sentiments along with specific emotions like happiness, anger, or sadness.",
    examples=[
        "Analyze the sentiment of these customer reviews",
        "What's the general feeling about our product on social media?",
        "Analyze the emotional tone of this feedback"
    ]
)

# 3. Create an agent with this capability
agent_data = {
    "name": "SentimentAnalyst",
    "description": "Specializes in analyzing sentiment in text",
    "system_prompt": "You are a sentiment analysis specialist...",
    "framework": "autogen",
    "capabilities": [
        {
            "name": "sentiment_analysis",
            "description": "Can analyze sentiment and emotions in text",
            "parameters": {
                "languages": ["english", "spanish"],
                "sentiment_scale": "positive-negative"
            }
        }
    ],
    "config": {"llm_config": {"model": "gpt-4"}}
}

# 4. Register the agent (in a real scenario)
import requests
# requests.post("http://localhost:8000/agents", json=agent_data)
```

With this extension, the AMS will now recognize sentiment analysis tasks and select appropriate agents for them.

## 2. Adding New Agent Frameworks

To integrate a new agent framework with AMS, you need to:

### 2.1 Add the Framework to the AgentFramework Enum

In `ams/core/registry/models.py`, extend the `AgentFramework` enum:

```python
class AgentFramework(str, Enum):
    AUTOGEN = "autogen"
    CREWAI = "crewai"
    NEW_FRAMEWORK = "new_framework"  # Add your new framework here
```

### 2.2 Create a Framework Adapter

Create a new adapter class that implements the `FrameworkAdapter` interface:

```python
# ams/core/adapters/new_framework_adapter.py

from ..registry.models import AgentMetadata, AgentStatus, AgentCapability
from .base import FrameworkAdapter

class NewFrameworkAdapter(FrameworkAdapter):
    """Adapter for integrating the NewFramework with AMS."""
    
    async def initialize_agent(self, metadata: AgentMetadata) -> Any:
        """Initialize an agent using the NewFramework."""
        # Framework-specific initialization code
        pass

    async def execute_agent(self, agent: Any, task: str, messages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Execute a task using the NewFramework agent."""
        # Framework-specific execution code
        pass

    async def get_agent_status(self, agent: Any) -> AgentStatus:
        """Get the status of a NewFramework agent."""
        pass

    async def terminate_agent(self, agent: Any) -> bool:
        """Terminate a NewFramework agent."""
        pass

    async def get_agent_capabilities(self, agent: Any) -> Dict[str, Any]:
        """Get the capabilities of the NewFramework agent."""
        pass
```

### 2.3 Register the Adapter

In `ams/core/adapters/__init__.py`, add your adapter to the registry:

```python
from .new_framework_adapter import NewFrameworkAdapter

# Registry of adapters for different frameworks
ADAPTER_REGISTRY: Dict[AgentFramework, Type[FrameworkAdapter]] = {
    AgentFramework.AUTOGEN: AutoGenAdapter,
    AgentFramework.CREWAI: CrewAIAdapter,
    AgentFramework.NEW_FRAMEWORK: NewFrameworkAdapter,  # Add your adapter here
}
```

### 2.4 Using the New Framework

After registering, you can create agents using your new framework:

```python
agent_data = {
    "name": "NewFrameworkAgent",
    "description": "An agent using the new framework",
    "system_prompt": "You are a new framework agent.",
    "framework": "new_framework",  # Use the framework name from the enum
    "capabilities": [...],
    "config": {...}
}
```

## 3. Extending the Supervisor Logic

### 3.1 Customizing Agent Selection

Override the `select_agents` method in a custom supervisor to change how agents are selected for tasks:

```python
class CustomSupervisor(SupervisorManager):
    async def select_agents(self, task_analysis: Dict[str, Any]) -> List[AgentMetadata]:
        # Custom agent selection logic
        # For example, incorporating domain-specific knowledge
        
        domain = task_analysis.get("domain", "general")
        if domain == "healthcare":
            # Select healthcare-specific agents
            return await self._select_healthcare_agents(task_analysis)
        elif domain == "finance":
            # Select finance-specific agents
            return await self._select_finance_agents(task_analysis)
        else:
            # Use the default agent selection for other domains
            return await super().select_agents(task_analysis)
```

### 3.2 Customizing Execution Order

Override the `determine_agent_execution_order` method to implement custom execution ordering:

```python
async def determine_agent_execution_order(self, agents: List[AgentMetadata]) -> List[AgentMetadata]:
    # Custom ordering logic
    # For example, based on specific business rules
    
    # Always put research agents first
    researchers = []
    others = []
    
    for agent in agents:
        is_researcher = False
        if agent.capabilities:
            for capability in agent.capabilities:
                if "research" in capability.name:
                    is_researcher = True
                    break
        
        if is_researcher:
            researchers.append(agent)
        else:
            others.append(agent)
    
    return researchers + others
```

## 4. Adding Custom Communication Methods

### 4.1 Extending the CommunicationHub

Create a subclass of `CommunicationHub` with additional features:

```python
from ams.core.communication.hub import CommunicationHub

class ExtendedCommunicationHub(CommunicationHub):
    """Extended communication hub with additional features."""
    
    def __init__(self):
        super().__init__()
        self.external_connections = {}
    
    def connect_external_system(self, system_id: str, connection_info: Dict[str, Any]) -> bool:
        """Connect to an external communication system."""
        # Implementation for external system integration
        pass
        
    def send_external_message(self, system_id: str, content: str, sender_id: str) -> bool:
        """Send a message to an external system."""
        # Implementation for external messaging
        pass
```

## 5. Creating New Agent Types

### 5.1 Specialized Agent Templates

Create specialized agent templates for common patterns:

```python
def create_research_agent(name: str, research_domain: str) -> Dict[str, Any]:
    """Create a research agent for a specific domain."""
    return {
        "name": f"{name}",
        "description": f"Research specialist in {research_domain}",
        "system_prompt": f"You are a research specialist in {research_domain}. Your role is to find and analyze information in this domain.",
        "framework": "autogen",
        "capabilities": [
            {
                "name": "research",
                "description": f"Can perform research in {research_domain}",
                "parameters": {"domain": research_domain}
            }
        ],
        "config": {
            "execution_priority": 1,
            "llm_config": {
                "model": "gpt-4", 
                "temperature": 0.7
            }
        }
    }
```

## 6. Integrating with External Systems

### 6.1 Custom Tools and APIs

Create custom tools for agents to interact with external APIs:

```python
def create_agent_with_external_tools(name: str, api_key: str) -> Dict[str, Any]:
    """Create an agent with access to external APIs."""
    return {
        "name": name,
        "description": "Agent with external API access",
        "system_prompt": "You have access to external APIs and tools.",
        "framework": "autogen",
        "capabilities": [
            {
                "name": "external_api_access",
                "description": "Can access external APIs",
                "parameters": {"api_type": "weather"}
            }
        ],
        "config": {
            "api_credentials": {
                "api_key": api_key
            },
            "llm_config": {
                "model": "gpt-4",
                "temperature": 0.3
            }
        }
    }
```

## 7. Best Practices for Extension

1. **Follow the Interface**: Always implement all required methods in the framework adapter.
2. **Error Handling**: Implement robust error handling for all external integrations.
3. **Documentation**: Document your extensions clearly, especially custom capabilities.
4. **Testing**: Create test cases for your extensions to ensure they work with the rest of the system.
5. **Versioning**: Consider versioning your extensions for backward compatibility.

## Conclusion

The Agent Management Server is designed to be extensible at multiple levels. By following these patterns, you can customize and extend the system to fit your specific needs while maintaining compatibility with the core functionality. 