# AMS API Reference

This document provides detailed information about the REST API endpoints available in the Agent Management Server (AMS).

## Base URL

By default, the AMS API is accessible at:

```
http://localhost:8000
```

You can configure a different host and port using the configuration options described in the README.

## Authentication

Authentication is configurable and can be enabled or disabled via the `security.enable_auth` configuration option.

When enabled, you need to include an authentication token in the request headers:

```
Authorization: Bearer your-token-here
```

## API Endpoints

### Agent Management

#### Register an Agent

Register a new agent with the AMS.

- **URL**: `/agents`
- **Method**: `POST`
- **Request Body**:

```json
{
  "name": "string",
  "description": "string",
  "system_prompt": "string",
  "framework": "string",
  "capabilities": [
    {
      "name": "string",
      "description": "string",
      "parameters": {}
    }
  ],
  "config": {
    "llm_config": {
      "model": "string",
      "temperature": 0.7
    }
  }
}
```

- **Response**:

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "system_prompt": "string",
  "framework": "string",
  "capabilities": [
    {
      "name": "string",
      "description": "string",
      "parameters": {}
    }
  ],
  "config": {},
  "created_at": "string",
  "updated_at": "string"
}
```

#### Get All Agents

Retrieve a list of all registered agents.

- **URL**: `/agents`
- **Method**: `GET`
- **Response**:

```json
[
  {
    "id": "string",
    "name": "string",
    "description": "string",
    "system_prompt": "string",
    "framework": "string",
    "capabilities": [],
    "config": {},
    "created_at": "string",
    "updated_at": "string"
  }
]
```

#### Get Agent by ID

Retrieve a specific agent by its ID.

- **URL**: `/agents/{agent_id}`
- **Method**: `GET`
- **Response**:

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "system_prompt": "string",
  "framework": "string",
  "capabilities": [],
  "config": {},
  "created_at": "string",
  "updated_at": "string"
}
```

#### Delete Agent

Remove an agent from the registry.

- **URL**: `/agents/{agent_id}`
- **Method**: `DELETE`
- **Response**:

```json
{
  "success": true,
  "message": "Agent deleted successfully"
}
```

### Task Management

#### Create a Task

Create a new task for agents to collaborate on.

- **URL**: `/tasks`
- **Method**: `POST`
- **Request Body**:

```json
{
  "task": "string",
  "agent_ids": ["string"],  // Optional
  "config": {}  // Optional
}
```

- **Response**:

```json
{
  "task_id": "string",
  "session_id": "string",
  "task": "string",
  "status": "created",
  "created_at": "string"
}
```

#### Get Task Status

Check the status of a task.

- **URL**: `/tasks/{session_id}`
- **Method**: `GET`
- **Response**:

```json
{
  "task_id": "string",
  "session_id": "string",
  "task": "string",
  "status": "string",
  "created_at": "string",
  "completed_at": "string"
}
```

#### Execute Task

Start executing a task.

- **URL**: `/tasks/{session_id}/execute`
- **Method**: `POST`
- **Response**:

```json
{
  "session_id": "string",
  "status": "executing",
  "message": "Task execution started"
}
```

#### Get Session Messages

Retrieve all messages from a collaboration session.

- **URL**: `/tasks/{session_id}/messages`
- **Method**: `GET`
- **Response**:

```json
[
  {
    "id": "string",
    "session_id": "string",
    "sender_id": "string",
    "sender_name": "string",
    "content": "string",
    "timestamp": "string",
    "metadata": {}
  }
]
```

#### Send Message to Session

Send a message to a collaboration session.

- **URL**: `/tasks/{session_id}/messages`
- **Method**: `POST`
- **Request Body**:

```json
{
  "sender_id": "string",
  "content": "string",
  "metadata": {}  // Optional
}
```

- **Response**:

```json
{
  "id": "string",
  "session_id": "string",
  "sender_id": "string",
  "sender_name": "string",
  "content": "string",
  "timestamp": "string",
  "metadata": {}
}
```

### Capability Management

#### Get All Capabilities

Get information about all registered capabilities.

- **URL**: `/capabilities`
- **Method**: `GET`
- **Response**:

```json
[
  {
    "name": "string",
    "description": "string",
    "examples": ["string"]
  }
]
```

#### Register Capability

Register a new capability in the system.

- **URL**: `/capabilities`
- **Method**: `POST`
- **Request Body**:

```json
{
  "name": "string",
  "description": "string",
  "examples": ["string"]
}
```

- **Response**:

```json
{
  "name": "string",
  "description": "string",
  "examples": ["string"],
  "created_at": "string"
}
```

### System Information

#### Health Check

Check if the server is running.

- **URL**: `/health`
- **Method**: `GET`
- **Response**:

```json
{
  "status": "healthy",
  "version": "string",
  "uptime": "string"
}
```

#### Server Configuration

Get information about the server configuration.

- **URL**: `/config`
- **Method**: `GET`
- **Response**:

```json
{
  "server": {
    "host": "string",
    "port": 8000,
    "workers": 4
  },
  "database": {
    "url": "string",
    "echo": false
  },
  "security": {
    "enable_auth": true
  }
}
```

## Error Handling

All API endpoints use a consistent error response format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

Common error codes:

- `400`: Bad Request - The request was invalid or cannot be served
- `401`: Unauthorized - Authentication is required
- `404`: Not Found - The resource does not exist
- `500`: Internal Server Error - An error occurred on the server

## Pagination

For endpoints that return multiple items, pagination is supported with the following query parameters:

- `limit`: Maximum number of items to return (default: 100)
- `offset`: Number of items to skip (default: 0)

Example:

```
GET /agents?limit=10&offset=20
```

This retrieves agents 21-30 from the registry. 