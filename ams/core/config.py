"""
Configuration Module

This module manages the configuration settings for the AMS system.
It supports loading configuration from environment variables, config files,
and provides default values.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from enum import Enum
from dataclasses import dataclass, field, asdict

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger(__name__)

# Environment variable prefix for all AMS settings
ENV_PREFIX = "AMS_"


class LogLevel(str, Enum):
    """Supported log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ServerConfig:
    """Configuration for the HTTP server"""
    host: str = field(
        default_factory=lambda: os.getenv(f"{ENV_PREFIX}HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.getenv(f"{ENV_PREFIX}PORT", "8000"))
    )
    reload: bool = field(
        default_factory=lambda: os.getenv(f"{ENV_PREFIX}RELOAD", "false").lower() in ("true", "1", "yes")
    )
    log_level: LogLevel = field(
        default_factory=lambda: LogLevel(os.getenv(f"{ENV_PREFIX}LOG_LEVEL", "info").lower())
    )
    workers: int = field(
        default_factory=lambda: int(os.getenv(f"{ENV_PREFIX}WORKERS", "1"))
    )


@dataclass
class DatabaseConfig:
    """Configuration for database connections"""
    url: str = field(
        default_factory=lambda: os.getenv(f"{ENV_PREFIX}DATABASE_URL", "sqlite:///ams.db")
    )
    echo: bool = field(
        default_factory=lambda: os.getenv(f"{ENV_PREFIX}DATABASE_ECHO", "false").lower() in ("true", "1", "yes")
    )
    pool_size: int = field(
        default_factory=lambda: int(os.getenv(f"{ENV_PREFIX}DATABASE_POOL_SIZE", "5"))
    )


@dataclass
class SecurityConfig:
    """Configuration for security features"""
    secret_key: str = field(
        default_factory=lambda: os.getenv(f"{ENV_PREFIX}SECRET_KEY", "supersecretkey")
    )
    token_expiration: int = field(
        default_factory=lambda: int(os.getenv(f"{ENV_PREFIX}TOKEN_EXPIRATION", "1440"))
    )
    enable_auth: bool = field(
        default_factory=lambda: os.getenv(f"{ENV_PREFIX}ENABLE_AUTH", "false").lower() in ("true", "1", "yes")
    )
    
    def __post_init__(self):
        """Validate that the secret key is strong enough"""
        if self.secret_key == "supersecretkey":
            logger.warning("Using default secret key. This is not secure for production!")
        if len(self.secret_key) < 16:
            logger.warning("Secret key is too short. It should be at least 16 characters long.")


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: str = field(
        default_factory=lambda: os.getenv(f"{ENV_PREFIX}LLM_PROVIDER", "openai")
    )
    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv(f"{ENV_PREFIX}LLM_API_KEY")
    )
    default_model: str = field(
        default_factory=lambda: os.getenv(f"{ENV_PREFIX}LLM_DEFAULT_MODEL", "gpt-4")
    )
    temperature: float = field(
        default_factory=lambda: float(os.getenv(f"{ENV_PREFIX}LLM_TEMPERATURE", "0.7"))
    )
    max_tokens: Optional[int] = field(
        default_factory=lambda: int(os.getenv(f"{ENV_PREFIX}LLM_MAX_TOKENS", "0")) or None
    )


@dataclass
class Config:
    """Main configuration for the AMS system"""
    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "Config":
        """
        Load configuration from a YAML file
        
        Args:
            file_path: Path to the YAML configuration file
            
        Returns:
            A Config object with settings from the file
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Config file {file_path} not found, using default settings")
            return cls()
        
        try:
            with open(path, "r") as f:
                config_data = yaml.safe_load(f)
            
            # Create config based on the loaded data
            server_config = ServerConfig(**config_data.get("server", {}))
            database_config = DatabaseConfig(**config_data.get("database", {}))
            security_config = SecurityConfig(**config_data.get("security", {}))
            llm_config = LLMConfig(**config_data.get("llm", {}))
            
            return cls(
                server=server_config,
                database=database_config,
                security=security_config,
                llm=llm_config
            )
        except Exception as e:
            logger.error(f"Error loading config from {file_path}: {e}")
            logger.warning("Using default settings")
            return cls()
    
    def setup_logging(self) -> None:
        """Configure the logging system based on settings"""
        logging.basicConfig(
            level=getattr(logging, self.server.log_level.name),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary"""
        return {
            "server": asdict(self.server),
            "database": asdict(self.database),
            "security": asdict(self.security),
            "llm": asdict(self.llm),
        }


# Create a global config instance
config = Config()


def load_config(file_path: Optional[Union[str, Path]] = None) -> Config:
    """
    Load and initialize the configuration
    
    Args:
        file_path: Optional path to a YAML configuration file
        
    Returns:
        The initialized Config object
    """
    global config
    
    if file_path:
        config = Config.from_file(file_path)
    
    # Setup logging according to configuration
    config.setup_logging()
    
    return config 