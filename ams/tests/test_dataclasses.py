#!/usr/bin/env python3
"""
End-to-end test script for dataclasses in AMS.

This script verifies that our migration from Pydantic to dataclasses works correctly,
including configuration loading and API model serialization/deserialization.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from dataclasses import asdict
import yaml

# Add the parent directory to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import our dataclass-based modules
from ams.core.config import Config, ServerConfig, DatabaseConfig, SecurityConfig, LLMConfig
from ams.api.models import (
    AgentCapabilityModel,
    AgentRegistrationRequest,
    AgentResponse,
    TaskRequest,
    TaskResponse,
    MessageRequest,
    MessageResponse
)

def test_config_dataclasses():
    """Test configuration dataclasses."""
    print("\n=== Testing Configuration Dataclasses ===")
    
    # Test default config
    config = Config()
    print(f"Default config created: ✅")
    
    # Test to_dict method
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert "server" in config_dict
    print(f"Config.to_dict() works: ✅")
    
    # Test from environment variables
    os.environ["AMS_HOST"] = "127.0.0.1"
    os.environ["AMS_PORT"] = "9000"
    os.environ["AMS_LOG_LEVEL"] = "debug"
    
    config = Config()
    assert config.server.host == "127.0.0.1"
    assert config.server.port == 9000
    print(f"Config from environment variables works: ✅")
    
    # Test from YAML file
    config_data = {
        "server": {
            "host": "localhost",
            "port": 8080,
            "workers": 4
        },
        "database": {
            "url": "postgresql://user:pass@localhost/db"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp:
        yaml.dump(config_data, temp)
        temp_path = temp.name
    
    try:
        config = Config.from_file(temp_path)
        assert config.server.host == "localhost"
        assert config.server.port == 8080
        assert config.server.workers == 4
        assert config.database.url == "postgresql://user:pass@localhost/db"
        print(f"Config from YAML file works: ✅")
    finally:
        Path(temp_path).unlink()
    
    # Test asdict conversion
    config = Config()
    config_dict = asdict(config)
    assert isinstance(config_dict, dict)
    print(f"asdict conversion works: ✅")
    
    print("All configuration tests passed!\n")


def test_api_models_dataclasses():
    """Test API model dataclasses."""
    print("\n=== Testing API Model Dataclasses ===")
    
    # Test AgentCapabilityModel
    capability = AgentCapabilityModel(
        name="test_capability",
        description="A test capability"
    )
    capability_dict = asdict(capability)
    assert capability_dict["name"] == "test_capability"
    print(f"AgentCapabilityModel works: ✅")
    
    # Test AgentRegistrationRequest
    agent_request = AgentRegistrationRequest(
        name="Test Agent",
        description="A test agent",
        system_prompt="You are a test agent",
        framework="autogen",
        capabilities=[capability],
        config={"key": "value"}
    )
    agent_request_dict = asdict(agent_request)
    assert agent_request_dict["name"] == "Test Agent"
    assert len(agent_request_dict["capabilities"]) == 1
    print(f"AgentRegistrationRequest works: ✅")
    
    # Test creating from dict
    agent_json = {
        "name": "JSON Agent",
        "description": "Created from JSON",
        "system_prompt": "You are a JSON agent",
        "framework": "crewai"
    }
    agent_from_json = AgentRegistrationRequest(**agent_json)
    assert agent_from_json.name == "JSON Agent"
    print(f"Creating from dict works: ✅")
    
    # Test AgentResponse
    agent_response = AgentResponse(
        id="agent-123",
        name="Response Agent",
        description="A response agent",
        framework="autogen",
        status="ready",
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z"
    )
    agent_response_dict = asdict(agent_response)
    assert agent_response_dict["id"] == "agent-123"
    print(f"AgentResponse works: ✅")
    
    # Test TaskRequest and TaskResponse
    task_request = TaskRequest(task="Test task")
    task_response = TaskResponse(
        session_id="session-123",
        task="Test task",
        agents=["agent-1", "agent-2"]
    )
    assert asdict(task_request)["task"] == "Test task"
    assert asdict(task_response)["session_id"] == "session-123"
    print(f"Task models work: ✅")
    
    # Test MessageRequest and MessageResponse
    message_request = MessageRequest(
        content="Test message",
        sender_id="user-1",
        sender_name="User"
    )
    message_response = MessageResponse(
        message_id="msg-123",
        content="Response message",
        sender_id="agent-1",
        sender_name="Agent",
        timestamp="2023-01-01T00:00:00Z"
    )
    assert asdict(message_request)["content"] == "Test message"
    assert asdict(message_response)["message_id"] == "msg-123"
    print(f"Message models work: ✅")
    
    print("All API model tests passed!\n")


def test_json_serialization():
    """Test JSON serialization and deserialization."""
    print("\n=== Testing JSON Serialization ===")
    
    # Create a model
    agent = AgentRegistrationRequest(
        name="JSON Test Agent",
        description="Testing JSON serialization",
        system_prompt="You are a test agent",
        framework="autogen",
        capabilities=[
            AgentCapabilityModel(
                name="json_capability",
                description="A JSON capability"
            )
        ]
    )
    
    # Convert to dict and then JSON
    agent_dict = asdict(agent)
    agent_json = json.dumps(agent_dict)
    
    # Convert back from JSON to dict to object
    parsed_dict = json.loads(agent_json)
    
    # We need to manually convert nested dataclasses
    # Convert capabilities dicts back to AgentCapabilityModel objects
    if parsed_dict.get("capabilities"):
        parsed_dict["capabilities"] = [
            AgentCapabilityModel(**cap_dict) 
            for cap_dict in parsed_dict["capabilities"]
        ]
    
    # Now create the main object
    parsed_agent = AgentRegistrationRequest(**parsed_dict)
    
    # Verify
    assert parsed_agent.name == "JSON Test Agent"
    assert len(parsed_agent.capabilities) == 1
    assert parsed_agent.capabilities[0].name == "json_capability"
    print(f"JSON serialization/deserialization works: ✅")
    
    print("All JSON serialization tests passed!\n")


if __name__ == "__main__":
    print("=== Testing AMS Dataclasses ===")
    test_config_dataclasses()
    test_api_models_dataclasses()
    test_json_serialization()
    print("\n=== All Tests Passed ✅ ===")
    print("The migration from Pydantic to dataclasses is working correctly!") 