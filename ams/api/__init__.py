"""
API Module

This module provides the REST API interface for the Agent Management Server.
It exposes endpoints for agent registration, task creation, session management,
and other core functionalities of the system.

Components:
- app: FastAPI application with all defined routes and endpoints
- models: Pydantic models for API request/response validation
- routes: Individual API endpoint route definitions
- middleware: API middleware components for request/response processing
"""

from fastapi import FastAPI
from .app import create_app

# Create the FastAPI application
app = create_app()

__all__ = ["app"] 