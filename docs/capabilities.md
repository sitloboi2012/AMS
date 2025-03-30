# Agent Capabilities

This document explains how capabilities work in the Agent Management Server (AMS) and how to use them effectively in your agent designs.

## What Are Capabilities?

In AMS, capabilities are declarative descriptions of what an agent can do. They serve as:

1. **Metadata for Agent Selection**: Help the system identify which agents can handle specific tasks
2. **Documentation for Users**: Communicate what each agent is designed to do
3. **Semantic Matching Criteria**: Allow the supervisor to match tasks to appropriate agents

Each capability consists of:

- **Name**: A unique identifier (e.g., "code_execution", "data_analysis")  
- **Description**: A human-readable explanation of what the capability does
- **Parameters** (optional): Additional configuration for the capability

## Core System Capabilities

AMS comes with several built-in capability types:

| Capability | Description |
|------------|-------------|
| `text_generation` | Can generate coherent and contextually relevant text |
| `code_generation` | Can write, analyze, and debug code in various languages |
| `code_execution` | Can execute code and interpret the results |
| `data_analysis` | Can analyze and interpret complex data sets |
| `research` | Can find and synthesize information from various sources |
| `math` | Can solve mathematical problems and perform calculations |
| `planning` | Can break down complex tasks into steps and create action plans |
| `reasoning` | Can engage in logical reasoning to solve problems |
| `creative` | Can generate creative and original content |

## Registering Agents with Capabilities

When registering an agent with AMS, you can specify its capabilities:

```python
agent_data = {
    "name": "CodeExpert",
    "description": "An agent specialized in writing and debugging code",
    "system_prompt": "You are an expert software developer...",
    "framework": "autogen",
    "capabilities": [
        {
            "name": "code_generation",
            "description": "Can write efficient and clean code"
        },
        {
            "name": "code_execution",
            "description": "Can execute and debug code",
            "parameters": {
                "languages": ["python", "javascript", "java"],
                "execution_environment": "sandboxed"
            }
        }
    ],
    "config": {
        "llm_config": {
            "model": "gpt-4",
            "temperature": 0.2
        }
    }
}

# Register with the AMS API
response = requests.post("http://localhost:8000/agents", json=agent_data)
```

## How Capabilities Are Used

### 1. Task Analysis

When a new task is submitted to AMS, the system analyzes it to determine what capabilities are required:

```python
# This is internal to AMS
required_capabilities = await capability_registry.get_required_capabilities(
    "Write a Python script to analyze stock market data and predict trends"
)

# Might return: ["code_generation", "data_analysis"]
```

### 2. Agent Selection

The supervisor uses the required capabilities to select appropriate agents:

```python
# This is internal to AMS
matched_agents = await capability_registry.filter_agents_by_capabilities(
    agents=available_agents,
    task="Write a Python script to analyze stock market data and predict trends"
)
```

### 3. Collaboration Planning

The supervisor uses capabilities to determine agent execution order and dependencies:

```python
# The data analyst should go first to determine what to analyze
# Then the code expert can implement the analysis
execution_order = [
    data_analyst_agent,  # Has data_analysis capability
    code_expert_agent    # Has code_generation capability
]
```

## Capability Matching System

AMS uses a semantic matching system to determine which capabilities are required for a task. This is more sophisticated than simple keyword matching:

1. **LLM-Based Analysis**: Uses language models to understand the task semantically
2. **Example-Based Learning**: Uses examples to improve matching accuracy
3. **Confidence Scoring**: Assigns confidence scores to potential capability matches

### How Capability Matching Works

The AMS capability registry provides a method to analyze a task:

```python
# Internal to AMS
scores = await capability_registry.analyze_capabilities_with_llm(
    "Create a visualization of customer purchase patterns"
)

# Might return:
# {
#   "data_analysis": 0.92,
#   "code_generation": 0.78,
#   "research": 0.45,
#   ...
# }
```

Capabilities with scores above a threshold are considered required for the task.

## Creating Custom Capabilities

You can extend AMS with custom capabilities to represent specialized skills:

```python
from ams.core.registry.capability_registry import capability_registry

# Register a new capability
capability_registry.register_capability(
    capability_name="sentiment_analysis",
    description="Ability to analyze and determine sentiment in text data. Can detect positive, negative, and neutral emotions, as well as specific emotional states.",
    examples=[
        "Analyze the sentiment of these customer reviews",
        "What's the emotional tone of this feedback?",
        "Determine how people feel about our new product launch",
        "Identify the prevailing sentiment in these social media posts"
    ]
)
```

The examples help the system learn when this capability is needed.

## Best Practices for Capabilities

### 1. Be Specific but Not Too Narrow

- **Good**: "financial_analysis" for specialized financial tasks
- **Too Narrow**: "stock_market_prediction" might be too specific
- **Too Broad**: "analysis" is too general to be useful

### 2. Use Clear Descriptions

Good capability descriptions:
- Clearly state what the capability enables
- Mention specific domains or contexts
- Include limitations or constraints
- Are understandable by non-experts

### 3. Use Parameters for Configuration

Parameters allow you to specify details about a capability:

```python
"capabilities": [
    {
        "name": "data_analysis",
        "description": "Specializes in statistical analysis",
        "parameters": {
            "data_types": ["time_series", "categorical"],
            "preferred_tools": ["pandas", "numpy"],
            "techniques": ["regression", "classification"]
        }
    }
]
```

### 4. Create Complementary Capabilities

Design capability sets that work well together:

- **Research + Summarization**: One agent researches, another summarizes findings
- **Planning + Execution**: One agent creates plans, another implements them
- **Creative + Refinement**: One agent generates creative ideas, another refines them

## Capability Examples for Common Use Cases

### Content Creation Team

```python
# Expert Writer
{
    "name": "content_creation",
    "description": "Can create high-quality written content on various topics",
    "parameters": {
        "content_types": ["blog", "article", "social_media"],
        "tone": ["professional", "casual", "educational"]
    }
}

# Editor
{
    "name": "content_refinement",
    "description": "Can edit and improve written content for clarity and style",
    "parameters": {
        "focus_areas": ["grammar", "clarity", "structure", "engagement"]
    }
}

# SEO Specialist
{
    "name": "seo_optimization",
    "description": "Can optimize content for search engines",
    "parameters": {
        "techniques": ["keyword_analysis", "metadata_optimization"]
    }
}
```

### Software Development Team

```python
# Architect
{
    "name": "system_design",
    "description": "Can design software architecture and system components",
    "parameters": {
        "domains": ["web", "mobile", "distributed_systems"]
    }
}

# Developer
{
    "name": "code_generation",
    "description": "Can write clean, efficient code",
    "parameters": {
        "languages": ["python", "javascript", "typescript", "java"],
        "paradigms": ["object_oriented", "functional"]
    }
}

# Tester
{
    "name": "code_testing",
    "description": "Can create and execute test cases",
    "parameters": {
        "testing_types": ["unit", "integration", "end_to_end"]
    }
}
```

## Advanced Capability Features

### Capability Hierarchies

AMS supports capability hierarchies where more specialized capabilities can inherit from broader ones:

```python
# Register a parent capability
capability_registry.register_capability(
    capability_name="data_processing",
    description="General ability to process and handle data"
)

# Register specialized child capabilities
capability_registry.register_capability(
    capability_name="data_cleaning",
    description="Ability to clean and prepare datasets",
    parent="data_processing"
)

capability_registry.register_capability(
    capability_name="data_visualization",
    description="Ability to create visual representations of data",
    parent="data_processing"
)
```

When a task requires "data_processing", agents with child capabilities are also considered.

### Capability Requirements

You can specify that certain capabilities require others to be present:

```python
capability_registry.register_capability(
    capability_name="advanced_nlp",
    description="Advanced natural language processing techniques",
    requires=["text_generation", "data_analysis"]
)
```

This ensures that agents with "advanced_nlp" also have the required foundational capabilities.

## Conclusion

Capabilities are a powerful mechanism in AMS for matching agents to tasks and facilitating effective collaboration. By carefully designing agent capabilities, you can create specialized agents that work together seamlessly to accomplish complex tasks. 