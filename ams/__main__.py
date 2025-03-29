"""
Main entry point for the Agent Management Server.
"""

import argparse
import logging
import uvicorn

from . import __version__

def main() -> None:
    """Main entry point for the AMS server."""
    parser = argparse.ArgumentParser(description="Agent Management Server (AMS)")
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0", 
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload (development mode)"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        default="info", 
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (default: info)"
    )
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"AMS version {__version__}"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Log startup info
    logger = logging.getLogger("ams")
    logger.info(f"Starting Agent Management Server v{__version__}")
    logger.info(f"Server will be available at http://{args.host}:{args.port}")
    
    # Start the server
    uvicorn.run(
        "ams.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )

if __name__ == "__main__":
    main() 