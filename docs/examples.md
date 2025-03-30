# AMS Examples

This directory contains example scripts to demonstrate how to use the Agent Management Server (AMS).

## Prerequisites

Before running these examples, make sure:

1. The AMS server is running (typically on http://localhost:8000)
2. You have the required dependencies installed:
   ```bash
   pip install requests
   ```
3. Set your OpenAI API key in the environment:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

## Examples Overview

### 1. Register Agents (`register_agents.py`)

This script demonstrates how to register different types of agents with various capabilities:
- General-purpose assistant
- Code-focused assistant
- Creative writing assistant
- Data analysis assistant

Usage:
```bash
python register_agents.py
```

### 2. Create Tasks (`create_tasks.py`)

This script shows how to create and execute tasks in different ways:
- Creating a task and executing it separately
- Creating and executing a task in one step
- Creating a task that requires multiple capabilities

Usage:
```bash
python create_tasks.py
```

### 3. Multi-Agent Collaboration (`multi_agent_collaboration.py`)

This script demonstrates how to set up a complex task that requires collaboration between multiple specialized agents:
- Researcher agent for gathering information
- Writer agent for creating content
- Code writer agent for implementing solutions
- Critic agent for reviewing and providing feedback

Usage:
```bash
python multi_agent_collaboration.py
```

### 4. Mixed Framework Collaboration (`mixed_framework_collaboration.py`)

This script demonstrates how agents from different frameworks (AutoGen and CrewAI) can work together through the AMS:
- Registers agents from both AutoGen and CrewAI frameworks
- Creates a complex task requiring diverse capabilities
- Shows how agents from different frameworks collaborate
- Displays the conversation with framework information for each agent

Usage:
```bash
python mixed_framework_collaboration.py
```

## Example Workflow

A typical workflow for using the AMS might look like:

1. Register specialized agents for your needs
2. Create a task that requires those capabilities
3. Execute the task and let the AMS handle agent selection and orchestration
4. Retrieve and process the results

## Adapting Examples

Feel free to modify these examples to fit your specific use cases:

- Change the agent capabilities and system prompts
- Modify task descriptions to test different scenarios
- Experiment with different LLM configurations
- Create custom workflows with multiple agents

## Troubleshooting

If you encounter issues:

1. Ensure the AMS server is running
2. Check that your OpenAI API key is valid
3. Verify network connectivity to the AMS server
4. Check the AMS server logs for any errors s