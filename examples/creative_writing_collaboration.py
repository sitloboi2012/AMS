#!/usr/bin/env python3
"""
Creative Writing Collaboration Example

This script demonstrates a creative writing collaboration between AutoGen and CrewAI agents.
The agents work together to create a short story, with each agent handling different aspects
of the creative process:

1. CrewAIBrainstormer: Generates creative concepts, setting, and character ideas
2. AutoGenOutliner: Structures these ideas into a coherent narrative framework
3. CrewAIWriter: Transforms the outline into engaging prose with dialogue and descriptions
4. AutoGenEditor: Refines and polishes the final story for quality and coherence

This example showcases how specialized agents from different frameworks can collaborate
in a sequential workflow to produce creative content.
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, TypedDict, cast
from pathlib import Path
import socket

# Type hints for requests library to fix linter errors
try:
    import requests
    # requests library is available
except ImportError:
    # Only for type checking - stub class if requests is not available
    class Response:
        status_code: int
        text: str
        def json(self) -> Any: ...
    
    class requests:
        class RequestException(Exception): 
            pass
            
        @staticmethod
        def get(url: str, **kwargs: Any) -> 'Response': ...
        
        @staticmethod
        def post(url: str, **kwargs: Any) -> 'Response': ...

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("creative_writing")

# Configuration - will be auto-detected
AMS_URL = None
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DEFAULT_PORTS = [8000, 5000, 3000]  # Common ports to try

# Type definitions for better type checking
class AgentContribution(TypedDict):
    content: str
    framework: str
    timestamp: str
    role: str

class AgentResponse(TypedDict):
    id: str
    name: str
    description: str
    framework: str

def detect_ams_server() -> str:
    """
    Detect the AMS server by trying common ports.
    
    Returns:
        The AMS URL if detected, otherwise a default URL
    """
    # First, try to check if the environment variable is set
    if "AMS_URL" in os.environ:
        url = os.environ["AMS_URL"]
        logger.info(f"Using AMS_URL from environment: {url}")
        return url
    
    # Try common ports
    for port in DEFAULT_PORTS:
        url = f"http://localhost:{port}"
        try:
            # Check the root endpoint instead of /health
            response = requests.get(url, timeout=2)
            if response.status_code in [200, 404]:  # Either 200 OK or 404 Not Found means server is running
                logger.info(f"AMS server detected at {url}")
                return url
        except (requests.RequestException, socket.error):
            continue
    
    # Default to port 8000 if not found
    logger.warning("Could not auto-detect AMS server, using default http://localhost:8000")
    return "http://localhost:8000"

def setup_environment() -> bool:
    """
    Check if the environment is properly configured.
    
    Returns:
        bool: True if properly configured, False otherwise
    """
    global AMS_URL
    AMS_URL = detect_ams_server()
    
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable is not set")
        logger.info("Please set it with: export OPENAI_API_KEY=your_api_key")
        return False
        
    # Verify AMS is running
    try:
        # Check the root endpoint instead of /health
        response = requests.get(f"{AMS_URL}/")
        if response.status_code not in [200, 404]:  # Either 200 OK or 404 Not Found means server is running
            logger.error(f"AMS server not reachable at {AMS_URL}")
            logger.info("Please start the AMS server with: python -m ams")
            logger.info("Or run with: python -m ams --reload (for development)")
            return False
    except requests.RequestException:
        logger.error(f"AMS server not reachable at {AMS_URL}")
        logger.info("Please start the AMS server with: python -m ams")
        logger.info("Or run with: python -m ams --reload (for development)")
        return False
        
    return True

def register_creative_writing_agents() -> List[AgentResponse]:
    """
    Register agents specialized in different aspects of the creative writing process.
    
    Returns:
        List[AgentResponse]: List of registered agent data
    """
    logger.info("Registering creative writing agents...")
    
    agents_data: List[Dict[str, Any]] = [
        {
            "name": "CrewAIBrainstormer",
            "description": "Expert in generating creative concepts and ideas",
            "system_prompt": "You are a creative brainstormer who specializes in generating unique and interesting ideas for stories. Your role is to provide compelling concepts, settings, characters, and plot hooks.",
            "capabilities": [
                {
                    "name": "text_generation",
                    "description": "Can generate creative concepts and ideas"
                }
            ],
            "framework": "crewai",
            "config": {
                "execution_priority": 1,  # Execute first
                "llm_config": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.9
                },
                "role": "Creative Brainstormer",
                "goal": "Generate unique and compelling story concepts",
                "backstory": "An imaginative ideation specialist who can envision novel scenarios and concepts"
            }
        },
        {
            "name": "AutoGenOutliner",
            "description": "Expert in structuring and organizing narratives",
            "system_prompt": "You are a story outliner who excels at creating well-structured narrative outlines. Your role is to take creative concepts and organize them into a coherent story structure with a clear beginning, middle, and end.",
            "capabilities": [
                {
                    "name": "text_generation",
                    "description": "Can create structured narrative outlines"
                }
            ],
            "framework": "autogen",
            "config": {
                "execution_priority": 2,  # Execute second
                "depends_on": ["CrewAIBrainstormer"],  # Depends on brainstormer's ideas
                "llm_config": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        },
        {
            "name": "CrewAIWriter",
            "description": "Expert in creative prose and dialogue writing",
            "system_prompt": "You are a skilled creative writer who specializes in vivid prose and engaging dialogue. Your role is to transform outlines into captivating narrative text with rich descriptions and authentic character voices.",
            "capabilities": [
                {
                    "name": "text_generation",
                    "description": "Can write creative prose and dialogue"
                }
            ],
            "framework": "crewai",
            "config": {
                "execution_priority": 3,  # Execute third
                "depends_on": ["AutoGenOutliner"],  # Depends on the outliner's structure
                "llm_config": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.8
                },
                "role": "Creative Writer",
                "goal": "Transform outlines into engaging narrative text",
                "backstory": "A talented wordsmith with a gift for creating immersive story worlds through prose"
            }
        },
        {
            "name": "AutoGenEditor",
            "description": "Expert in refining and polishing written content",
            "system_prompt": "You are a skilled editor who specializes in refining and improving written content. Your role is to polish the narrative prose, correct inconsistencies, enhance the flow, and ensure the story is engaging from start to finish.",
            "capabilities": [
                {
                    "name": "text_generation",
                    "description": "Can edit and refine written content"
                }
            ],
            "framework": "autogen",
            "config": {
                "execution_priority": 4,  # Execute last
                "depends_on": ["CrewAIWriter"],  # Depends on the writer's draft
                "llm_config": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.4,
                    "max_tokens": 3000
                }
            }
        }
    ]
    
    registered_agents: List[AgentResponse] = []
    
    for agent_data in agents_data:
        try:
            response = requests.post(f"{AMS_URL}/agents", json=agent_data)
            
            if response.status_code == 200:
                result = cast(AgentResponse, response.json())
                logger.info(f"Successfully registered: {agent_data['name']} ({agent_data['framework']})")
                registered_agents.append(result)
            else:
                logger.error(f"Failed to register {agent_data['name']}: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Exception during agent registration: {str(e)}")
    
    return registered_agents

def create_writing_task(task_description: str) -> Dict[str, Any]:
    """
    Create a creative writing task that requires collaboration.
    
    Args:
        task_description: Description of the writing task
        
    Returns:
        Dict[str, Any]: Task data with session ID
    """
    logger.info("Creating creative writing task...")
    
    try:
        response = requests.post(
            f"{AMS_URL}/tasks", 
            headers={"Content-Type": "application/json"},
            json={"task": task_description}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Task created with session ID: {result['session_id']}")
            return cast(Dict[str, Any], result)
        else:
            logger.error(f"Failed to create task: {response.text}")
            return {}
    except requests.RequestException as e:
        logger.error(f"Exception during task creation: {str(e)}")
        return {}

def execute_creative_collaboration(session_id: str) -> Dict[str, AgentContribution]:
    """
    Execute the creative writing collaboration session.
    
    Args:
        session_id: The session ID for the collaboration
        
    Returns:
        Dict[str, AgentContribution]: Dictionary of agent contributions
    """
    logger.info(f"Starting creative writing collaboration session: {session_id}")
    print("\n=== Starting Creative Writing Collaboration ===")
    print("This example demonstrates the story creation process:")
    print("1. CrewAIBrainstormer → 2. AutoGenOutliner → 3. CrewAIWriter → 4. AutoGenEditor")
    print("Each agent contributes a different aspect to the creative writing process.")
    
    # Start the collaboration
    try:
        response = requests.post(f"{AMS_URL}/tasks/{session_id}/execute")
        
        if response.status_code != 200:
            logger.error(f"Failed to start session: {response.text}")
            return {}
        
        logger.info("Collaboration session started successfully")
        print("✅ Session started successfully! Monitoring progress...")
        
        # Monitor the collaboration by checking messages
        last_message_count = 0
        wait_time = 0
        max_wait_time = 600  # Maximum wait time in seconds (10 minutes)
        
        # Store the agent contributions for final display
        agent_contributions: Dict[str, AgentContribution] = {}
        
        # Get initial list of registered agents to map IDs to names
        agents_response = requests.get(f"{AMS_URL}/agents")
        agent_name_map: Dict[str, str] = {}
        if agents_response.status_code == 200:
            agents_data = agents_response.json()
            agent_name_map = {agent["id"]: agent["name"] for agent in agents_data}
        
        print("\n--- Collaboration Progress ---")
        
        while wait_time < max_wait_time:
            # Get messages
            messages_response = requests.get(f"{AMS_URL}/tasks/{session_id}/messages")
            
            if messages_response.status_code == 200:
                messages: List[Dict[str, Any]] = messages_response.json()
                
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
                            "timestamp": msg.get("timestamp", ""),
                            "role": get_agent_role(sender_name)
                        }
                        
                        # Print a notification about the new contribution
                        preview = content[:150] + "..." if len(content) > 150 else content
                        print(f"\n➤ {sender_name} ({framework.upper()}) has contributed:")
                        print(f"  \"{preview}\"")
                        logger.info(f"New contribution from {sender_name} ({framework})")
                    
                    last_message_count = len(messages)
                    wait_time = 0  # Reset wait time when there's activity
                    
                    # Check if all agents have contributed
                    expected_agents = ["CrewAIBrainstormer", "AutoGenOutliner", "CrewAIWriter", "AutoGenEditor"]
                    if all(agent in agent_contributions for agent in expected_agents):
                        logger.info("All agents have contributed to the collaboration")
                        print("\n✅ All agents have contributed to the story!")
                        break
                else:
                    print(".", end="", flush=True)
                    time.sleep(5)
                    wait_time += 5
                    
            else:
                logger.error(f"Failed to get messages: {messages_response.text}")
                print(f"\nFailed to get messages: {messages_response.text}")
                time.sleep(5)
                wait_time += 5
                
        if wait_time >= max_wait_time:
            logger.warning("Monitoring timed out, collaboration may still be in progress")
            print("\n⚠️ Monitoring timed out, but the task may still be running.")
        
        return agent_contributions
        
    except requests.RequestException as e:
        logger.error(f"Exception during collaboration execution: {str(e)}")
        return {}

def get_agent_role(agent_name: str) -> str:
    """
    Get a descriptive role for an agent based on its name.
    
    Args:
        agent_name: The name of the agent
        
    Returns:
        str: The descriptive role for the agent
    """
    roles = {
        "CrewAIBrainstormer": "CONCEPT GENERATOR",
        "AutoGenOutliner": "STORY ARCHITECT",
        "CrewAIWriter": "NARRATIVE AUTHOR", 
        "AutoGenEditor": "CONTENT REFINER"
    }
    return roles.get(agent_name, "CONTRIBUTOR")

def print_final_story(agent_contributions: Dict[str, AgentContribution]) -> None:
    """
    Print the final story with clear separation between different agent contributions.
    
    Args:
        agent_contributions: Dictionary mapping agent names to their contributions
    """
    if not agent_contributions:
        logger.warning("No agent contributions to display")
        return
        
    logger.info("Displaying final story with all agent contributions")
    print("\n\n============================================")
    print("           THE FINISHED STORY               ")
    print("============================================\n")
    
    # Print each contribution in the expected order
    for agent_name in ["CrewAIBrainstormer", "AutoGenOutliner", "CrewAIWriter", "AutoGenEditor"]:
        if agent_name in agent_contributions:
            contrib = agent_contributions[agent_name]
            role = contrib.get("role", "CONTRIBUTOR")
            framework = contrib.get("framework", "unknown").upper()
            
            print(f"\n=== {role} ({agent_name} - {framework}) ===\n")
            
            if agent_name == "AutoGenEditor":
                # For the editor, this is the final story
                print("FINAL STORY:\n")
                print(contrib["content"])
                print("\n" + "="*50)
            else:
                # For other agents, display their contribution
                print(contrib["content"])
    
    print("\nThe story creation process is complete!")

def save_story_to_file(agent_contributions: Dict[str, AgentContribution], filename: Optional[str] = None) -> None:
    """
    Save the final edited story to a file.
    
    Args:
        agent_contributions: Dictionary mapping agent names to their contributions
        filename: Name of the file to save the story to (default: generated_story.txt)
    """
    if not filename:
        # Create a timestamped filename
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"generated_story_{timestamp}.txt"
    
    # Ensure the filename has a .txt extension
    if not filename.endswith(".txt"):
        filename += ".txt"
    
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / filename
    
    if "AutoGenEditor" in agent_contributions:
        final_story = agent_contributions["AutoGenEditor"]["content"]
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("GENERATED STORY\n")
                f.write("==============\n\n")
                f.write(final_story)
                
            logger.info(f"Story saved to {filepath}")
            print(f"\nStory saved to {filepath}")
        except IOError as e:
            logger.error(f"Error saving story to file: {str(e)}")
            print(f"\nError saving story to file: {str(e)}")
    else:
        logger.warning("Editor's contribution not found, cannot save final story")
        print("\nCouldn't save story: Editor's contribution not found")

def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    """
    Get all messages from a collaboration session.
    
    Args:
        session_id: The session ID
        
    Returns:
        List[Dict[str, Any]]: List of messages
    """
    try:
        logger.info(f"Retrieving messages for session {session_id}")
        response = requests.get(f"{AMS_URL}/tasks/{session_id}/messages")
        
        if response.status_code == 200:
            return cast(List[Dict[str, Any]], response.json())
        else:
            logger.error(f"Failed to get session messages: {response.text}")
            return []
    except requests.RequestException as e:
        logger.error(f"Exception retrieving session messages: {str(e)}")
        return []

def main() -> None:
    """Main execution function for the creative writing collaboration example."""
    print("=== Creative Writing Collaboration Example ===")
    logger.info("Starting Creative Writing Collaboration Example")
    
    # Setup environment
    if not setup_environment():
        return
    
    # Register creative writing agents
    registered_agents = register_creative_writing_agents()
    if not registered_agents:
        logger.error("Failed to register agents, exiting")
        return
    
    # Create a task that requires collaborative story creation
    story_prompt = """
    Develop a short story (around 1000 words) that combines elements of science fiction and mystery. 
    The story should involve:
    
    1. A character who discovers something unexpected about their seemingly ordinary world
    2. An unusual piece of technology that plays a central role in the plot
    3. A mysterious event or phenomenon that needs to be resolved
    
    The story should have a clear beginning, middle, and end, with a satisfying resolution to the mystery.
    
    IMPORTANT: Each agent should contribute their specialist expertise to the creative process:
    - The Brainstormer should generate creative concepts, setting, and character ideas
    - The Outliner should structure these ideas into a coherent narrative framework
    - The Writer should transform the outline into engaging prose with dialogue and descriptions
    - The Editor should refine and polish the final story for quality and coherence
    
    This is a collaborative creative process where each agent builds upon the previous contributions.
    """
    
    task_result = create_writing_task(story_prompt)
    
    if not task_result:
        logger.error("Failed to create task, exiting")
        return
    
    session_id = task_result["session_id"]
    
    # Execute the creative writing collaboration
    agent_contributions = execute_creative_collaboration(session_id)
    
    if not agent_contributions:
        logger.error("No agent contributions collected, exiting")
        return
    
    # Display the results
    print_final_story(agent_contributions)
    
    # Save the final story to a file
    save_story_to_file(agent_contributions)
    
    logger.info("Creative Writing Collaboration Example completed successfully")
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main() 