#!/usr/bin/env python3
"""
This script demonstrates how agents from different frameworks (AutoGen and CrewAI)
can collaborate on a task through the Agent Management Server (AMS).

Note: There may be compatibility issues with CrewAI agents in the current version.
If you encounter errors with CrewAI agents, try the following:
1. Check that the CrewAI version is compatible with the AMS
2. Ensure all required fields (role, goal, backstory) are properly configured
3. Check the CrewAI adapter implementation in the AMS codebase
"""

import os
import time
from typing import Dict, List, Any

import requests

# Configuration
AMS_URL = "http://localhost:8000"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_api_key")

if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY environment variable is not set")
    print("Please set it with: export OPENAI_API_KEY=your_api_key")
    exit(1)

def register_mixed_framework_agents() -> List[Dict[str, Any]]:
    """
    Register agents from different frameworks (AutoGen and CrewAI).
    
    Returns:
        List[Dict[str, Any]]: List of registered agent data
    """
    agents_data = [
        {
            "name": "AutoGenResearcher",
            "description": "Research specialist that finds and analyzes information",
            "system_prompt": "You are a skilled researcher who excels at finding and analyzing information. Your goal is to gather relevant data and provide insights based on your research.",
            "capabilities": [
                {
                    "name": "text_generation",
                    "description": "Can generate research reports and analysis"
                },
                {
                    "name": "data_analysis",
                    "description": "Can analyze and interpret data"
                }
            ],
            "framework": "autogen",
            "config": {
                "execution_priority": 1,  # Execute first
                "llm_config": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        },
        {
            "name": "CrewAIStrategist",
            "description": "Strategic planning expert that develops structured approaches to problems",
            "system_prompt": "You are a strategic planner who excels at developing structured approaches to complex problems. Your goal is to create clear, actionable plans based on available information.",
            "capabilities": [
                {
                    "name": "text_generation",
                    "description": "Can develop strategic plans and approaches"
                }
            ],
            "framework": "crewai",
            "config": {
                "execution_priority": 2,  # Execute second
                "llm_config": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.5
                },
                "role": "Strategic Planner",
                "goal": "Develop effective strategies based on market information",
                "backstory": "An experienced strategic planner with expertise in market analysis and positioning"
            }
        },
        {
            "name": "AutoGenWriter",
            "description": "Content creation specialist that produces well-written documents",
            "system_prompt": "You are a skilled writer who excels at creating well-structured, clear, and engaging content. Your goal is to transform ideas and information into compelling written materials.",
            "capabilities": [
                {
                    "name": "text_generation",
                    "description": "Can create high-quality written content"
                }
            ],
            "framework": "autogen",
            "config": {
                "execution_priority": 3,  # Execute third
                "depends_on": ["AutoGenResearcher", "CrewAIStrategist"],  # Explicit dependency
                "llm_config": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.8,
                    "max_tokens": 3000
                }
            }
        },
        {
            "name": "CrewAIEvaluator",
            "description": "Critical assessment specialist that reviews content quality",
            "system_prompt": "You are an evaluator who specializes in critical assessment. Your goal is to review content for accuracy, completeness, and quality, providing specific feedback for improvement.",
            "capabilities": [
                {
                    "name": "text_generation",
                    "description": "Can evaluate and provide feedback on content"
                }
            ],
            "framework": "crewai",
            "config": {
                "execution_priority": 4,  # Execute last
                "depends_on": ["AutoGenWriter"],  # Explicit dependency
                "llm_config": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.3
                },
                "role": "Evaluator",
                "goal": "Provide comprehensive and constructive feedback",
                "backstory": "A dedicated evaluator with a background in quality assessment and critical analysis"
            }
        }
    ]
    
    registered_agents = []
    
    for agent_data in agents_data:
        response = requests.post(f"{AMS_URL}/agents", json=agent_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Successfully registered: {agent_data['name']} ({agent_data['framework']})")
            registered_agents.append(result)
        else:
            print(f"Failed to register {agent_data['name']}: {response.text}")
    
    return registered_agents

def create_mixed_collaboration_task(task_description: str) -> Dict[str, Any]:
    """
    Create a task that requires collaboration between agents from different frameworks.
    
    Args:
        task_description: Description of the task to be performed
        
    Returns:
        Dict[str, Any]: Task data with session ID
    """
    response = requests.post(
        f"{AMS_URL}/tasks", 
        headers={"Content-Type": "application/json"},
        json={"task": task_description}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Task created with session ID: {result['session_id']}")
        return result
    else:
        print(f"Failed to create task: {response.text}")
        return {}

def execute_collaboration(session_id: str) -> None:
    """
    Execute the collaboration session.
    
    Args:
        session_id: The session ID for the collaboration
    """
    print("\n=== Starting Mixed Framework Collaboration Session ===")
    print("This example demonstrates how AutoGen and CrewAI agents work together in sequence:")
    print("1. AutoGenResearcher → 2. CrewAIStrategist → 3. AutoGenWriter → 4. CrewAIEvaluator")
    print("Each agent builds upon the work of previous agents, creating a collaborative workflow.")
    print("\nExecuting collaboration session...")
    
    # Start the collaboration
    response = requests.post(f"{AMS_URL}/tasks/{session_id}/execute")
    
    if response.status_code != 200:
        print(f"Failed to start session: {response.text}")
        return
    
    print("✅ Session started successfully!")
    print("Agents will now collaborate in the specified execution order.")
    print("This may take a few minutes as agents process the conversation history and respond.")
    
    # Monitor the collaboration by checking messages
    last_message_count = 0
    wait_time = 0
    max_wait_time = 300  # Maximum wait time in seconds (5 minutes)
    
    # Store the agent contributions for final display
    agent_contributions = {}
    
    # Get initial list of registered agents to map IDs to names
    agents_response = requests.get(f"{AMS_URL}/agents")
    agent_name_map = {}
    if agents_response.status_code == 200:
        agents_data = agents_response.json()
        agent_name_map = {agent["id"]: agent["name"] for agent in agents_data}
    
    print("\n--- Collaboration Progress ---")
    
    while wait_time < max_wait_time:
        # Get messages
        messages_response = requests.get(f"{AMS_URL}/tasks/{session_id}/messages")
        
        if messages_response.status_code == 200:
            messages = messages_response.json()
            
            # If we have new messages, update and print
            if len(messages) > last_message_count:
                # Process any new messages
                for i in range(last_message_count, len(messages)):
                    msg = messages[i]
                    sender_id = msg.get("sender_id", "")
                    sender_name = msg.get("sender_name", "Unknown")
                    content = msg.get("content", "")
                    
                    # Skip system messages
                    if sender_id == "system":
                        continue
                    
                    # Get the framework of the agent
                    framework = "unknown"
                    if "metadata" in msg and "framework" in msg["metadata"]:
                        framework = msg["metadata"]["framework"]
                    
                    # Store the contribution
                    agent_contributions[sender_name] = {
                        "content": content,
                        "framework": framework,
                        "timestamp": msg.get("timestamp", "")
                    }
                    
                    # Print a notification about the new contribution
                    preview = content[:100] + "..." if len(content) > 100 else content
                    print(f"\n➤ {sender_name} ({framework.upper()}) has contributed:")
                    print(f"  \"{preview}\"")
                
                last_message_count = len(messages)
                wait_time = 0  # Reset wait time when there's activity
                
                # Check if all agents have contributed
                agent_ids = [agent_id for agent_id in agent_name_map.keys()]
                contributor_ids = [msg.get("sender_id") for msg in messages]
                
                if all(agent_id in contributor_ids for agent_id in agent_ids):
                    print("\n✅ All agents have contributed to the collaboration!")
                    break
            else:
                print(".", end="", flush=True)
                time.sleep(3)
                wait_time += 3
                
        else:
            print(f"\nFailed to get messages: {messages_response.text}")
            time.sleep(3)
            wait_time += 3
            
    if wait_time >= max_wait_time:
        print("\n⚠️ Monitoring timed out, but the task may still be running.")
    
    # Display the final collaboration results
    print("\n\n=== Final Collaboration Results ===")
    for agent_name in ["AutoGenResearcher", "CrewAIStrategist", "AutoGenWriter", "CrewAIEvaluator"]:
        if agent_name in agent_contributions:
            contrib = agent_contributions[agent_name]
            print(f"\n--- {agent_name} ({contrib['framework'].upper()}) ---")
            # Print the first 300 characters of each contribution
            preview = contrib["content"][:300] + "..." if len(contrib["content"]) > 300 else contrib["content"]
            print(preview)
    
    print("\nFor the complete results, use the get_session_messages() function.")
    return

def get_registered_agents() -> List[Dict[str, Any]]:
    """
    Get all registered agents from the AMS.
    
    Returns:
        List[Dict[str, Any]]: List of registered agents
    """
    response = requests.get(f"{AMS_URL}/agents")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get registered agents: {response.text}")
        return []

def display_agent_summary(agents: List[Dict[str, Any]]) -> None:
    """
    Display a summary of all registered agents.
    
    Args:
        agents: List of agent data
    """
    print("\n===== Registered Agents =====")
    
    for agent in agents:
        framework = agent.get("framework", "unknown")
        print(f"- {agent['name']} ({framework.upper()}): {agent['description']}")
        
        capabilities = agent.get("capabilities", [])
        capability_names = [cap.get("name", "unknown") for cap in capabilities] if capabilities else []
        if capability_names:
            print(f"  Capabilities: {', '.join(capability_names)}")
    
    print("=============================\n")

def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    """
    Get all messages from a collaboration session.
    
    Args:
        session_id: The session ID
        
    Returns:
        List[Dict[str, Any]]: List of messages
    """
    response = requests.get(f"{AMS_URL}/tasks/{session_id}/messages")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get session messages: {response.text}")
        return []

def display_conversation(messages: List[Dict[str, Any]], agents: List[Dict[str, Any]]) -> None:
    """
    Display the conversation in a readable format with framework information.
    
    Args:
        messages: List of messages from the session
        agents: List of registered agents
    """
    if not messages:
        print("No messages found in the session.")
        return
    
    # Create a mapping of agent_id to framework for quick lookup
    agent_framework_map = {agent["id"]: agent.get("framework", "unknown") for agent in agents}
    
    print("\n===== Collaboration Conversation =====")
    
    for msg in messages:
        sender = msg.get("sender_name", "Unknown")
        sender_id = msg.get("sender_id")
        framework = agent_framework_map.get(sender_id, "system").upper() if sender_id else "SYSTEM"
        content = msg.get("content", "")
        
        # Clean up content if it looks like a serialized object
        if content and isinstance(content, str):
            # If it looks like a dictionary that was converted to a string
            if content.startswith('{') and content.endswith('}'):
                try:
                    import json
                    parsed = json.loads(content)
                    if isinstance(parsed, dict) and 'result' in parsed:
                        content = parsed['result']
                except:
                    pass
        
        print(f"\n[{framework}] {sender}:")
        print(f"{content}")
    
    print("\n=====================================\n")

def main() -> None:
    """Main execution function."""
    print("=== Mixed Framework Collaboration Example ===")
    
    # Register mixed framework agents
    register_mixed_framework_agents()
    
    # Get all registered agents for display
    agents = get_registered_agents()
    display_agent_summary(agents)
    
    # Create a task that requires collaboration
    task_description = """
    Develop a comprehensive market analysis for a new smart home product. This task requires:
    1. Research on current market trends and competitors (requiring research skills)
    2. Strategic planning for market positioning (requiring strategic planning expertise)
    3. Creating a well-written executive summary (requiring content creation and writing skills)
    4. A quality assessment of the final report (requiring evaluation capabilities)
    
    IMPORTANT: Each agent should build upon the work of previous agents. The researcher should provide data, 
    the strategist should develop plans based on that research, the writer should incorporate both 
    the research and strategic plans, and the evaluator should assess the complete work.
    
    This is a truly collaborative task where each agent contributes their expertise while building on the work of others.
    """
    
    task_result = create_mixed_collaboration_task(task_description)
    
    if not task_result:
        return
    
    session_id = task_result["session_id"]
    
    # Execute the collaboration
    execute_collaboration(session_id)
    
    # Display the conversation with framework information
    messages = get_session_messages(session_id)
    display_conversation(messages, agents)
    
    print("Example completed successfully!")

if __name__ == "__main__":
    main() 