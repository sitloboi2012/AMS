from datetime import datetime

from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field


class AgentFramework(str, Enum):
    AUTOGEN = "autogen"
    CREWAI = "crewai"


class AgentStatus(str, Enum):
    READY = "ready"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class AgentCapability:
    name: str
    description: str
    parameters: Optional[dict] = None


@dataclass
class AgentMetadata:
    id: str
    name: str
    description: str
    system_prompt: str
    framework: AgentFramework
    capabilities: Optional[List[AgentCapability]] = None
    status: AgentStatus = AgentStatus.OFFLINE
    config: Optional[dict] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
