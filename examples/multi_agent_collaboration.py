#!/usr/bin/env python
"""
Example script for setting up multi-agent collaboration with the AMS.
This demonstrates how to create a task that requires multiple agents to collaborate.
"""

import requests
import time
from typing import Dict, Any, List, Union

# Configuration
AMS_URL = "http://localhost:8000"

def register_specialized_agents() -> List[dict]:
    """Register specialized agents for collaboration."""
    agents = [
        # Researcher agent
        {
            "name": "Researcher",
            "description": "An agent that specializes in research and information gathering",
            "system_prompt": "You are a research specialist. Your role is to gather and analyze information on various topics. Be thorough, accurate, and comprehensive in your research.",
            "framework": "autogen",
            "capabilities": [
                {
                    "name": "text_generation",
                    "description": "Can research and gather information"
                }
            ],
            "config": {
                "llm_config": {
                    "model": "gpt-4",
                    "temperature": 0.3
                }
            }
        },
        # Writer agent
        {
            "name": "Writer",
            "description": "An agent that specializes in writing compelling content",
            "system_prompt": "You are a skilled writer. Your role is to craft engaging, clear, and well-structured content based on the information provided. Focus on creating compelling narratives.",
            "framework": "autogen",
            "capabilities": [
                {
                    "name": "text_generation",
                    "description": "Can write engaging content"
                }
            ],
            "config": {
                "llm_config": {
                    "model": "gpt-4",
                    "temperature": 0.7
                }
            }
        },
        # Code writer agent
        {
            "name": "CodeWriter",
            "description": "An agent that specializes in writing code",
            "system_prompt": "You are an expert software developer. Your role is to write clean, efficient, and well-documented code based on requirements. Focus on creating maintainable and optimized solutions.",
            "framework": "autogen",
            "capabilities": [
                {
                    "name": "code_execution",
                    "description": "Can write efficient code"
                }
            ],
            "config": {
                "llm_config": {
                    "model": "gpt-4",
                    "temperature": 0.2
                }
            }
        },
        # Critic agent
        {
            "name": "Critic",
            "description": "An agent that specializes in reviewing and critiquing work",
            "system_prompt": "You are a thoughtful critic. Your role is to review and provide constructive feedback on content and code. Focus on identifying potential improvements and issues.",
            "framework": "autogen",
            "capabilities": [
                {
                    "name": "text_generation",
                    "description": "Can review and critique content"
                },
                {
                    "name": "code_execution",
                    "description": "Can review and critique code"
                }
            ],
            "config": {
                "llm_config": {
                    "model": "gpt-4",
                    "temperature": 0.4
                }
            }
        }
    ]
    
    registered_agents = []
    for agent_data in agents:
        response = requests.post(
            f"{AMS_URL}/agents", 
            headers={"Content-Type": "application/json"},
            json=agent_data
        )
        
        if response.status_code == 200:
            registered_agent = response.json()
            print(f"Registered {agent_data['name']} with ID: {registered_agent['id']}")
            registered_agents.append(registered_agent)
        else:
            print(f"Failed to register {agent_data['name']}: {response.text}")
    
    return registered_agents

def create_collaboration_session(task_description: str) -> Union[dict, None]:
    """Create a task that requires collaboration between multiple agents."""
    response = requests.post(
        f"{AMS_URL}/tasks", 
        headers={"Content-Type": "application/json"},
        json={"task": task_description}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Created collaboration session with ID: {data['session_id']}")
        print(f"Selected agents: {', '.join(data['agents'])}")
        return data
    else:
        print(f"Failed to create collaboration session: {response.text}")
        return None

def send_message_to_session(session_id: str, content: str, sender_id: str, sender_name: str) -> Union[dict, None]:
    """Send a message to the collaboration session."""
    response = requests.post(
        f"{AMS_URL}/tasks/{session_id}/messages",
        headers={"Content-Type": "application/json"},
        json={
            "content": content,
            "sender_id": sender_id,
            "sender_name": sender_name
        }
    )
    
    if response.status_code == 200:
        print(f"Sent message from {sender_name} to session {session_id}")
        return response.json()
    else:
        print(f"Failed to send message: {response.text}")
        return None

def get_messages(session_id: str) -> List[dict]:
    """Get all messages from the collaboration session."""
    response = requests.get(f"{AMS_URL}/tasks/{session_id}/messages")
    
    if response.status_code == 200:
        messages = response.json()
        print(f"Retrieved {len(messages)} messages from session {session_id}")
        return messages
    else:
        print(f"Failed to get messages: {response.text}")
        return []

def display_conversation(messages: List[Dict[str, Any]]) -> None:
    """Display the conversation in a readable format."""
    print("\n=== Collaboration Conversation ===")
    for i, message in enumerate(messages):
        sender = message.get('sender_name', 'Unknown')
        content = message.get('content', 'No content')
        
        print(f"\n--- Message {i+1} from {sender} ---")
        print(content[:500] + "..." if len(content) > 500 else content)

def execute_collaboration(session_id: str) -> Union[dict, None]:
    """Execute the collaboration session."""
    response = requests.post(f"{AMS_URL}/tasks/{session_id}/execute")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Successfully executed collaboration session: {session_id}")
        print(f"Status: {data['status']}")
        return data
    else:
        print(f"Failed to execute collaboration: {response.text}")
        return None

def main() -> None:
    # Step 1: Register specialized agents
    print("Registering specialized agents for collaboration...\n")
    registered_agents = register_specialized_agents()
    
    # Step 2: Create a collaboration task that requires multiple agents
    # This task requires research, code writing, and critique
    print("\nCreating a collaboration task...\n")
    complex_task = (
        "Create a web application that visualizes climate change data. "
        "This task requires research on climate change data sources, "
        "writing code to fetch and process the data, and creating visualizations. "
        "The final output should include research findings, code implementation, "
        "and a critique of the approach. This is both a research, coding, and writing task."
    )
    
    session_data = create_collaboration_session(complex_task)
    if not session_data:
        print("Failed to create collaboration session. Exiting.")
        return
    
    session_id = session_data['session_id']
    
    # Step 3: Execute the collaboration
    print("\nExecuting the collaboration...\n")
    execution_data = execute_collaboration(session_id)
    
    # Step 4: Wait a moment and then get the conversation
    print("\nWaiting for agents to collaborate...")
    time.sleep(2)
    
    # Step 5: Get and display the conversation
    messages = get_messages(session_id)
    display_conversation(messages)
    
    # Step 6: Terminate the session when done
    print("\nTerminating the collaboration session...")
    requests.post(f"{AMS_URL}/tasks/{session_id}/terminate")
    print("Collaboration complete!")

if __name__ == "__main__":
    main() 