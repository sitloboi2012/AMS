#!/usr/bin/env python
"""
Example script for registering agents with the AMS.
This demonstrates how to register different types of agents with various capabilities.
"""

import os
import requests

from typing import Union

# Configuration
AMS_URL = "http://localhost:8000"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_api_key_here")

def register_agent(agent_data: dict) -> Union[dict, None]:
    """Register an agent with the AMS."""
    response = requests.post(
        f"{AMS_URL}/agents", 
        headers={"Content-Type": "application/json"},
        json=agent_data
    )
    
    if response.status_code == 200:
        print(f"Successfully registered agent: {agent_data['name']}")
        print(f"Agent ID: {response.json()['id']}")
        return response.json() # type: ignore
    else:
        print(f"Failed to register agent: {response.text}")
        return None

def main() -> None:
    # Example 1: Register a general-purpose assistant
    general_assistant = {
        "name": "GeneralAssistant",
        "description": "A general-purpose AI assistant",
        "system_prompt": "You are a helpful AI assistant. Answer questions accurately and concisely.",
        "framework": "autogen",
        "capabilities": [
            {
                "name": "text_generation",
                "description": "Can generate text responses based on prompts"
            }
        ],
        "config": {
            "llm_config": {
                "model": "gpt-4",
                "temperature": 0.7,
                "api_key": OPENAI_API_KEY
            }
        }
    }
    
    # Example 2: Register a code-focused assistant
    code_assistant = {
        "name": "CodeAssistant",
        "description": "An assistant specializing in programming and software development",
        "system_prompt": "You are an expert programmer with deep knowledge of multiple programming languages and software architectures. Write clean, efficient, and well-documented code.",
        "framework": "autogen",
        "capabilities": [
            {
                "name": "code_execution",
                "description": "Can generate and explain code"
            }
        ],
        "config": {
            "llm_config": {
                "model": "gpt-4",
                "temperature": 0.2,
                "api_key": OPENAI_API_KEY
            }
        }
    }
    
    # Example 3: Register a creative writing assistant
    writing_assistant = {
        "name": "WritingAssistant",
        "description": "An assistant specializing in creative writing",
        "system_prompt": "You are a skilled creative writer who can craft engaging stories, poems, and other written content. Be imaginative and use vivid language.",
        "framework": "autogen",
        "capabilities": [
            {
                "name": "text_generation",
                "description": "Can generate creative written content"
            }
        ],
        "config": {
            "llm_config": {
                "model": "gpt-4",
                "temperature": 0.9,
                "api_key": OPENAI_API_KEY
            }
        }
    }
    
    # Example 4: Register a data analysis assistant
    data_assistant = {
        "name": "DataAnalyst",
        "description": "An assistant specializing in data analysis",
        "system_prompt": "You are a data analyst with expertise in statistics and data visualization. Explain data concepts clearly and provide insightful analysis.",
        "framework": "autogen",
        "capabilities": [
            {
                "name": "data_analysis",
                "description": "Can analyze and interpret data"
            },
            {
                "name": "calculation",
                "description": "Can perform mathematical calculations"
            }
        ],
        "config": {
            "llm_config": {
                "model": "gpt-4",
                "temperature": 0.3,
                "api_key": OPENAI_API_KEY
            }
        }
    }
    
    # Register all agents
    agents = [general_assistant, code_assistant, writing_assistant, data_assistant]
    for agent in agents:
        register_agent(agent)
        print()  # Add a newline for readability
    
    # List all registered agents
    response = requests.get(f"{AMS_URL}/agents")
    if response.status_code == 200:
        print("All registered agents:")
        for agent in response.json():
            print(f"- {agent['name']} ({agent['id']}): {agent['framework']} - {agent['status']}")

if __name__ == "__main__":
    main() 