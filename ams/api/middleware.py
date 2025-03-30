"""
API Middleware

This module contains middleware components for the API, including:
- Error handling middleware
- Request logging
- Authentication and authorization
- Response standardization
"""

import time
import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.errors import AMSBaseException
from ..core.config import config

# Set up logging
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses.
    
    Logs details about incoming requests and outgoing responses,
    including timing information.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, log details, and pass to the next middleware.
        
        Args:
            request: The incoming HTTP request
            call_next: Function to call the next middleware
            
        Returns:
            The HTTP response
        """
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "-")
        
        # Log request details
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response details
            logger.info(
                f"Response {request_id}: {response.status_code} "
                f"processed in {process_time:.4f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            # Log exceptions
            process_time = time.time() - start_time
            logger.error(
                f"Error {request_id}: {str(e)} "
                f"occurred after {process_time:.4f}s"
            )
            raise


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Set up exception handlers for the FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """
        Handle HTTP exceptions and return a standardized error response.
        
        Args:
            request: The HTTP request
            exc: The HTTP exception
            
        Returns:
            A JSON response with error details
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": {}
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle validation errors and return a standardized error response.
        
        Args:
            request: The HTTP request
            exc: The validation error
            
        Returns:
            A JSON response with validation error details
        """
        # Extract error details
        error_details = []
        for error in exc.errors():
            error_details.append({
                "loc": error.get("loc", []),
                "msg": error.get("msg", ""),
                "type": error.get("type", "")
            })
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters",
                    "details": {
                        "errors": error_details
                    }
                }
            }
        )
    
    @app.exception_handler(AMSBaseException)
    async def ams_exception_handler(request: Request, exc: AMSBaseException) -> JSONResponse:
        """
        Handle AMS custom exceptions and return a standardized error response.
        
        Args:
            request: The HTTP request
            exc: The AMS exception
            
        Returns:
            A JSON response with error details
        """
        # Determine appropriate status code based on error type
        status_code = 500
        if hasattr(exc, "status_code"):
            status_code = exc.status_code
        elif exc.code.startswith("REGISTRY_"):
            status_code = 404 if "NOT_FOUND" in exc.code else 400
        elif exc.code.startswith("ADAPTER_"):
            status_code = 400
        elif exc.code.startswith("SUPERVISOR_"):
            status_code = 404 if "NOT_FOUND" in exc.code else 400
        elif exc.code.startswith("COMMUNICATION_"):
            status_code = 400
        
        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle all other exceptions and return a standardized error response.
        
        Args:
            request: The HTTP request
            exc: The exception
            
        Returns:
            A JSON response with error details
        """
        # Log unexpected exceptions
        logger.exception(f"Unhandled exception: {str(exc)}")
        
        # In non-development mode, hide detailed error messages
        error_message = str(exc)
        if not config.server.reload:  # Not in development mode
            error_message = "An unexpected error occurred"
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": error_message,
                    "details": {} if not config.server.reload else {"type": type(exc).__name__}
                }
            }
        )


def setup_middleware(app: FastAPI) -> None:
    """
    Set up all middleware for the FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Set up exception handlers
    setup_exception_handlers(app) 