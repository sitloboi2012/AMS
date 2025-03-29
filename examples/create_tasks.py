#!/usr/bin/env python
"""
Example script for creating and executing tasks with the AMS.
This demonstrates how to create tasks that will be matched with appropriate agents.
"""

import requests
import time
from typing import Dict, Any, List, Optional

# Configuration
AMS_URL = "http://localhost:8000"

def create_task(task_description: str) -> Optional[Dict[str, Any]]:
    """Create a task with the given description."""
    response = requests.post(
        f"{AMS_URL}/tasks", 
        headers={"Content-Type": "application/json"},
        json={"task": task_description}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Successfully created task: {task_description}")
        print(f"Session ID: {data['session_id']}")
        print(f"Selected agents: {', '.join(data['agents'])}")
        return data
    else:
        print(f"Failed to create task: {response.text}")
        return None

def execute_task(session_id: str) -> Optional[Dict[str, Any]]:
    """Execute a previously created task."""
    response = requests.post(f"{AMS_URL}/tasks/{session_id}/execute")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Successfully executed task for session: {session_id}")
        print(f"Status: {data['status']}")
        return data
    else:
        print(f"Failed to execute task: {response.text}")
        return None

def create_and_execute_task(task_description: str) -> Optional[Dict[str, Any]]:
    """Create and execute a task in one call."""
    response = requests.post(
        f"{AMS_URL}/tasks/run", 
        headers={"Content-Type": "application/json"},
        json={"task": task_description}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Successfully created and executed task: {task_description}")
        print(f"Session ID: {data['creation']['session_id']}")
        print(f"Status: {data['execution']['status']}")
        return data
    else:
        print(f"Failed to create and execute task: {response.text}")
        return None

def get_task_messages(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get all messages for a task session."""
    response = requests.get(f"{AMS_URL}/tasks/{session_id}/messages")
    
    if response.status_code == 200:
        messages = response.json()
        print(f"Retrieved {len(messages)} messages for session: {session_id}")
        return messages
    else:
        print(f"Failed to get messages: {response.text}")
        return None

def display_message_content(messages: List[Dict[str, Any]]) -> None:
    """Display the content of messages in a readable format."""
    for i, message in enumerate(messages):
        sender = message.get('sender_name', 'Unknown')
        content = message.get('content', 'No content')
        
        print(f"\nMessage {i+1} from {sender}:")
        print("-" * 40)
        print(content)
        print("-" * 40)

def main() -> None:
    # Example 1: Create a task and execute it separately
    print("EXAMPLE 1: Create and execute a task separately")
    print("=" * 50)
    task_data = create_task("Explain how quantum computing works in simple terms. This is a writing task.")
    
    if task_data:
        session_id = task_data['session_id']
        print("\nWaiting a moment before executing the task...")
        time.sleep(1)
        
        execution_data = execute_task(session_id)
        
        if execution_data:
            print("\nWaiting a moment before retrieving messages...")
            time.sleep(1)
            
            messages = get_task_messages(session_id)
            if messages:
                display_message_content(messages)
    
    # Example 2: Create and execute a task in one step
    print("\n\nEXAMPLE 2: Create and execute a task in one step")
    print("=" * 50)
    combined_data = create_and_execute_task(
        "Write a Python function to find all prime numbers up to a given limit. This is a programming task."
    )
    
    if combined_data:
        session_id = combined_data['creation']['session_id']
        print("\nWaiting a moment before retrieving messages...")
        time.sleep(1)
        
        messages = get_task_messages(session_id)
        if messages:
            display_message_content(messages)
    
    # Example 3: Create a task that requires multiple capabilities
    print("\n\nEXAMPLE 3: Create a task requiring multiple capabilities")
    print("=" * 50)
    combined_data = create_and_execute_task(
        "Analyze the following data and create a visualization: [1, 3, 5, 8, 13, 21, 34]. This is a data analysis task."
    )
    
    if combined_data:
        session_id = combined_data['creation']['session_id']
        print("\nWaiting a moment before retrieving messages...")
        time.sleep(1)
        
        messages = get_task_messages(session_id)
        if messages:
            display_message_content(messages)

if __name__ == "__main__":
    main() 