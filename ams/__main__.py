"""
Main entry point for the Agent Management Server.
"""

import argparse
import logging
import uvicorn
from pathlib import Path
from typing import Optional

from . import __version__
from .core.config import load_config, Config

logger = logging.getLogger("ams")

def main() -> None:
    """Main entry point for the AMS server."""
    parser = argparse.ArgumentParser(description="Agent Management Server (AMS)")
    parser.add_argument(
        "--host", 
        type=str, 
        help="Host to bind the server to (overrides config)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        help="Port to bind the server to (overrides config)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload (development mode, overrides config)"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (overrides config)"
    )
    parser.add_argument(
        "--config", 
        type=str,
        help="Path to configuration file (YAML format)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Number of worker processes (overrides config)"
    )
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"AMS version {__version__}"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config_path: Optional[Path] = None
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Config file not found: {args.config}")
            return
    
    # Load the config (from file if specified, otherwise from env vars)
    config = load_config(config_path)
    
    # Override config with command line arguments if provided
    if args.host:
        config.server.host = args.host
    if args.port:
        config.server.port = args.port
    if args.reload:
        config.server.reload = True
    if args.log_level:
        config.server.log_level = args.log_level
    if args.workers:
        config.server.workers = args.workers
    
    # Log startup info
    logger.info(f"Starting Agent Management Server v{__version__}")
    logger.info(f"Server will be available at http://{config.server.host}:{config.server.port}")
    
    # Start the server
    uvicorn.run(
        "ams.api:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
        log_level=config.server.log_level.value,
        workers=config.server.workers
    )

if __name__ == "__main__":
    main() 