#!/usr/bin/env python3
"""
Capability Extension Example

This script demonstrates how to extend the AMS system by adding a new capability.
It shows how to:
1. Register a new capability with the registry
2. Create an agent with the capability
3. Test the capability with various tasks
4. Demonstrate agent matching for tasks

The example creates a "sentiment_analysis" capability that can detect when a
task requires sentiment analysis and emotion detection.
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("capability_extension")

# Add the parent directory to path so we can import the ams module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import necessary AMS modules
from ams.core.registry.capability_registry import capability_registry
from ams.core.registry.models import AgentMetadata, AgentCapability, AgentFramework
from ams.core.adapters import get_adapter

# Step 1: Register the sentiment analysis capability with the registry
def register_sentiment_capability():
    """Register the sentiment analysis capability with the system."""
    capability_registry.register_capability(
        capability_name="sentiment_analysis",
        description="""
        Ability to analyze sentiment and emotions in text data. This includes:
        - Detecting positive, negative, or neutral sentiment
        - Identifying specific emotions like happiness, sadness, anger, fear, etc.
        - Analyzing emotional tone and intensity in communications
        - Understanding sentiment trends across multiple pieces of text
        - Detecting sarcasm, irony, and other complex sentiment patterns
        """,
        examples=[
            "Analyze the sentiment of these customer reviews",
            "What's the general feeling about our product launch on social media?",
            "Analyze the emotional tone in these customer service interactions",
            "Detect the sentiment trends in user feedback over the past month",
            "How do people feel about our new feature?",
            "Identify the emotional response to our recent announcement"
        ]
    )
    logger.info("Registered sentiment_analysis capability")
    
    # Print all registered capabilities to verify
    all_capabilities = capability_registry.get_all_capabilities()
    logger.info(f"All registered capabilities: {all_capabilities}")

# Step 2: Function to test the capability with various tasks
async def test_capability_with_tasks():
    """Test the capability with various tasks to see how it scores."""
    test_tasks = [
        "Perform sentiment analysis on customer reviews",
        "How do people feel about the new product launch?",
        "Write a report on quarterly sales figures",
        "Analyze the emotional response to the company announcement",
        "Create a Python script that calculates fibonacci numbers",
        "What's the sentiment around climate change on social media?",
        "Summarize the key points from these articles",
        "Track customer opinions and feelings about our service"
    ]
    
    print("\n=== Testing Sentiment Analysis Capability ===")
    print("Task | Capability Scores")
    print("-" * 60)
    
    for task in test_tasks:
        # Get capability scores for the task using LLM
        scores = await capability_registry.analyze_capabilities_with_llm(task)
        
        # Format the scores for display
        scores_str = ", ".join([f"{name}: {score:.2f}" for name, score in scores.items()])
        
        # Print the result
        print(f"'{task}' | {scores_str}")
    
    print("-" * 60)
    
    # Test the get_required_capabilities method
    sample_task = "Analyze the emotional tone and sentiment of these customer reviews"
    required_caps = await capability_registry.get_required_capabilities(sample_task)
    print(f"\nRequired capabilities for '{sample_task}':")
    print(required_caps)

# Step 3: Create an agent with the sentiment analysis capability
async def create_sentiment_analysis_agent():
    """Create a sample agent with sentiment analysis capability."""
    # Define the agent metadata
    metadata = AgentMetadata(
        id="sentiment-analyst-1",
        name="SentimentAnalyst",
        description="An agent specialized in sentiment analysis and emotion detection",
        system_prompt="You are an expert in analyzing sentiment and emotions in text. You can detect subtle nuances in language that convey feelings and attitudes.",
        framework=AgentFramework.AUTOGEN,
        capabilities=[
            AgentCapability(
                name="sentiment_analysis",
                description="Can analyze sentiment and emotions in text",
                parameters={
                    "languages": ["english", "spanish"],
                    "sentiment_scale": "positive-negative"
                }
            ),
            AgentCapability(
                name="text_generation",
                description="Can generate text responses"
            )
        ],
        config={
            "llm_config": {
                "model": "gpt-4-turbo",
                "temperature": 0.3
            }
        }
    )
    
    # Agent created - in a real scenario we would initialize it with the adapter
    logger.info(f"Created agent with sentiment_analysis capability: {metadata.name}")
    return metadata

# Step 4: Demonstrate agent matching with our new capability
async def demonstrate_agent_matching():
    """Show how agents with the new capability are matched to tasks."""
    # Create our sentiment analysis agent
    sentiment_agent = await create_sentiment_analysis_agent()
    
    # Create a mock agent without sentiment capabilities
    general_agent = AgentMetadata(
        id="general-assistant-1",
        name="GeneralAssistant",
        description="General purpose assistant",
        system_prompt="You are a helpful assistant.",
        framework=AgentFramework.AUTOGEN,
        capabilities=[
            AgentCapability(
                name="text_generation",
                description="Can generate text responses"
            )
        ],
        config={"llm_config": {"model": "gpt-4"}}
    )
    
    # Create a coding agent
    coding_agent = AgentMetadata(
        id="coding-expert-1",
        name="CodingExpert",
        description="Expert in writing code",
        system_prompt="You are a coding expert.",
        framework=AgentFramework.AUTOGEN,
        capabilities=[
            AgentCapability(
                name="code_generation",
                description="Can write and understand code"
            ),
            AgentCapability(
                name="text_generation",
                description="Can generate text responses"
            )
        ],
        config={"llm_config": {"model": "gpt-4"}}
    )
    
    # List of all agents
    all_agents = [sentiment_agent, general_agent, coding_agent]
    
    # Test tasks
    test_tasks = [
        "Analyze the sentiment of customer reviews from our last product launch",
        "Create a Python function to calculate prime numbers",
        "Write a summary of the quarterly report"
    ]
    
    print("\n=== Agent Selection Based on Capabilities ===")
    for task in test_tasks:
        print(f"\nTask: {task}")
        
        # Get matched agents for this task
        matched_agents = await capability_registry.filter_agents_by_capabilities(
            agents=all_agents,
            task=task
        )
        
        # Get the required capabilities for reference
        required_capabilities = await capability_registry.get_required_capabilities(task)
        print(f"Required capabilities: {required_capabilities}")
        
        print("Selected agents:")
        for agent in matched_agents:
            agent_capabilities = [cap.name for cap in agent.capabilities] if agent.capabilities else []
            print(f"- {agent.name} (capabilities: {agent_capabilities})")

# Main function
async def main():
    """Main function to demonstrate capability extension."""
    print("=== Extending AMS with Sentiment Analysis Capability ===")
    
    # Configure the capability registry's LLM settings if needed
    capability_registry.llm_config = {
        "model": "gpt-4o",  # or a different model if preferred
        "temperature": 0.1
    }
    
    # Register our new capability
    register_sentiment_capability()
    
    # Test the capability with various tasks
    await test_capability_with_tasks()
    
    # Demonstrate agent matching with the new capability
    await demonstrate_agent_matching()
    
    print("\n=== Capability Extension Demo Complete ===")

if __name__ == "__main__":
    asyncio.run(main()) 