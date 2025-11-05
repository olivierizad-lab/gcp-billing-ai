#!/usr/bin/env python3
"""
FastAPI backend server for the Agent Engine chat interface.

This server provides REST API endpoints for querying deployed Vertex AI Agent Engine agents.
It handles authentication and streams responses back to the frontend.
"""

import os
import json
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import google.auth
from google.auth.transport.requests import Request
import requests
from history import save_query, get_query_history, delete_query, delete_all_history

# Load environment variables
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env", override=False)

app = FastAPI(title="Agent Engine Chat API", version="1.0.0")

# CORS configuration - allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
PROJECT_ID = os.getenv("BQ_PROJECT") or os.getenv("GCP_PROJECT_ID", "qwiklabs-asl-04-8e9f23e85ced")
LOCATION = os.getenv("LOCATION", "us-central1")

# Load agent-specific .env files and extract REASONING_ENGINE_IDs
def load_agent_configs():
    """Load agent configurations from .env files."""
    configs = {}
    
    # bq_agent_mick - load from agent-specific .env, then check root env
    agent_mick_env = project_root / "bq_agent_mick" / ".env"
    mick_id = ""
    if agent_mick_env.exists():
        # Temporarily load to get REASONING_ENGINE_ID
        from dotenv import dotenv_values
        mick_env_vars = dotenv_values(agent_mick_env)
        mick_id = mick_env_vars.get("REASONING_ENGINE_ID", "")
    
    # Check root env for override (BQ_AGENT_MICK_REASONING_ENGINE_ID)
    mick_id = os.getenv("BQ_AGENT_MICK_REASONING_ENGINE_ID") or mick_id
    
    configs["bq_agent_mick"] = {
        "name": "bq_agent_mick",
        "display_name": "BigQuery Agent (Mick)",
        "description": "BigQuery billing data analysis agent",
        "reasoning_engine_id": mick_id,
    }
    
    # bq_agent - load from agent-specific .env, then check root env
    agent_env = project_root / "bq_agent" / ".env"
    agent_id = ""
    if agent_env.exists():
        from dotenv import dotenv_values
        agent_env_vars = dotenv_values(agent_env)
        agent_id = agent_env_vars.get("REASONING_ENGINE_ID", "")
    
    # Check root env for override (BQ_AGENT_REASONING_ENGINE_ID)
    agent_id = os.getenv("BQ_AGENT_REASONING_ENGINE_ID") or agent_id
    
    configs["bq_agent"] = {
        "name": "bq_agent",
        "display_name": "BigQuery Agent",
        "description": "BigQuery data analysis agent",
        "reasoning_engine_id": agent_id,
    }
    
    return configs

AGENT_CONFIGS = load_agent_configs()


class QueryRequest(BaseModel):
    message: str
    agent_name: str
    user_id: Optional[str] = "default_user"


class QueryResponse(BaseModel):
    response: str
    agent_name: str
    user_id: str
    query_id: Optional[str] = None


class HistoryItem(BaseModel):
    id: str
    user_id: str
    agent_name: str
    message: str
    response: str
    timestamp: str


class DeleteQueryRequest(BaseModel):
    query_id: str
    user_id: str


class AgentInfo(BaseModel):
    name: str
    display_name: str
    description: str
    reasoning_engine_id: str
    is_available: bool


def get_credentials():
    """Get Google Cloud credentials."""
    credentials, _ = google.auth.default()
    if not credentials.valid:
        credentials.refresh(Request())
    return credentials


def query_agent_stream(agent_name: str, message: str, user_id: str = "default_user"):
    """
    Stream query to the agent via Vertex AI REST API.
    
    Yields chunks of the response as they arrive.
    """
    # Get agent configuration
    if agent_name not in AGENT_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    agent_config = AGENT_CONFIGS[agent_name]
    reasoning_engine_id = agent_config["reasoning_engine_id"]
    
    if not reasoning_engine_id:
        raise HTTPException(
            status_code=400,
            detail=f"Agent '{agent_name}' is not configured. Please set REASONING_ENGINE_ID in .env file."
        )
    
    # Get credentials
    try:
        credentials = get_credentials()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get credentials: {str(e)}")
    
    # Build API endpoint
    base_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1"
    endpoint = f"{base_url}/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{reasoning_engine_id}:streamQuery"
    
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "input": {
            "message": message,
            "user_id": user_id
        }
    }
    
    try:
        # Stream the response
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            stream=True,
            timeout=180
        )
        
        if response.status_code != 200:
            error_text = response.text[:500]
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Agent query failed: {error_text}"
            )
        
        # Parse streaming JSON response
        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    data = json.loads(line)
                    # Extract text from response
                    content = data.get("content", {})
                    if isinstance(content, dict):
                        parts = content.get("parts", [])
                        for part in parts:
                            if isinstance(part, dict):
                                text = part.get("text")
                                if text:
                                    # Yield as Server-Sent Events format
                                    yield f"data: {json.dumps({'text': text})}\n\n"
                except json.JSONDecodeError:
                    # Skip non-JSON lines
                    pass
        
        # Send completion marker
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


def query_agent_stream_with_save(agent_name: str, message: str, user_id: str = "default_user"):
    """
    Stream query to agent and save to Firestore after completion.
    
    Yields chunks of the response and saves the complete query/response after streaming.
    """
    response_text = ""
    
    # Get agent configuration
    if agent_name not in AGENT_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    agent_config = AGENT_CONFIGS[agent_name]
    reasoning_engine_id = agent_config["reasoning_engine_id"]
    
    if not reasoning_engine_id:
        raise HTTPException(
            status_code=400,
            detail=f"Agent '{agent_name}' is not configured. Please set REASONING_ENGINE_ID in .env file."
        )
    
    # Get credentials
    try:
        credentials = get_credentials()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get credentials: {str(e)}")
    
    # Build API endpoint
    base_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1"
    endpoint = f"{base_url}/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{reasoning_engine_id}:streamQuery"
    
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "input": {
            "message": message,
            "user_id": user_id
        }
    }
    
    try:
        # Stream the response
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            stream=True,
            timeout=180
        )
        
        if response.status_code != 200:
            error_text = response.text[:500]
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Agent query failed: {error_text}"
            )
        
        # Parse streaming JSON response and collect text
        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    data = json.loads(line)
                    # Extract text from response
                    content = data.get("content", {})
                    if isinstance(content, dict):
                        parts = content.get("parts", [])
                        for part in parts:
                            if isinstance(part, dict):
                                text = part.get("text")
                                if text:
                                    response_text += text
                                    # Yield as Server-Sent Events format
                                    yield f"data: {json.dumps({'text': text})}\n\n"
                except json.JSONDecodeError:
                    # Skip non-JSON lines
                    pass
        
        # Save to Firestore after streaming completes
        if response_text:
            try:
                print(f"Saving query to Firestore: user_id={user_id}, agent={agent_name}, message_length={len(message)}, response_length={len(response_text)}")
                query_id = save_query(user_id, agent_name, message, response_text)
                print(f"Successfully saved query with ID: {query_id}")
                # Send query_id and completion marker
                yield f"data: {json.dumps({'query_id': query_id, 'done': True})}\n\n"
            except Exception as e:
                # Log error but don't fail the request
                import traceback
                error_details = traceback.format_exc()
                print(f"ERROR: Failed to save query to Firestore: {e}")
                print(f"Traceback: {error_details}")
                yield f"data: {json.dumps({'done': True, 'save_error': str(e)})}\n\n"
        else:
            # No response text, just send done marker
            print("Warning: No response text to save (empty response)")
            yield f"data: {json.dumps({'done': True})}\n\n"
        
    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Agent Engine Chat API",
        "version": "1.0.0",
        "agents": list(AGENT_CONFIGS.keys())
    }


@app.get("/agents", response_model=List[AgentInfo])
async def list_agents():
    """List all available agents."""
    agents = []
    for agent_name, config in AGENT_CONFIGS.items():
        agents.append(AgentInfo(
            name=config["name"],
            display_name=config["display_name"],
            description=config["description"],
            reasoning_engine_id=config["reasoning_engine_id"],
            is_available=bool(config["reasoning_engine_id"])
        ))
    return agents


@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    """
    Stream query to an agent and save to Firestore.
    
    Returns a Server-Sent Events (SSE) stream of response chunks.
    Query is automatically saved to Firestore after completion.
    """
    return StreamingResponse(
        query_agent_stream_with_save(request.agent_name, request.message, request.user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query an agent (non-streaming, returns complete response).
    
    Use /query/stream for streaming responses.
    """
    response_text = ""
    query_id = None
    try:
        for chunk in query_agent_stream_with_save(request.agent_name, request.message, request.user_id):
            if chunk.startswith("data: "):
                data_str = chunk[6:].strip()
                if data_str:
                    try:
                        data = json.loads(data_str)
                        if "text" in data:
                            response_text += data["text"]
                        if "query_id" in data:
                            query_id = data["query_id"]
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        pass
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
    
    return QueryResponse(
        response=response_text,
        agent_name=request.agent_name,
        user_id=request.user_id,
        query_id=query_id
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "project_id": PROJECT_ID, "location": LOCATION}


@app.get("/history")
async def get_history(user_id: str = "default_user", limit: int = 50):
    """
    Get query history for a user.
    
    Only returns history for the specified user_id.
    In production, user_id should come from authenticated session/IAP.
    
    Args:
        user_id: User ID (must be valid, sanitized)
        limit: Maximum number of queries to return (default: 50, max: 100)
    
    Returns:
        List of query history items (only for the specified user)
    """
    # Validate and sanitize user_id
    if not user_id or not isinstance(user_id, str):
        user_id = "default_user"
    
    # Sanitize: only allow alphanumeric, underscore, hyphen
    import re
    user_id = re.sub(r'[^a-zA-Z0-9_-]', '', user_id)
    if not user_id:
        user_id = "default_user"
    
    # Limit the limit parameter
    limit = min(max(1, limit), 100)
    
    try:
        # This will only return history for the specified user_id
        history = get_query_history(user_id, limit)
        # Ensure all items have required fields for HistoryItem
        validated_history = []
        for item in history:
            try:
                # Ensure all required fields are present
                validated_item = {
                    "id": item.get("id", ""),
                    "user_id": item.get("user_id", user_id),
                    "agent_name": item.get("agent_name", ""),
                    "message": item.get("message", ""),
                    "response": item.get("response", ""),
                    "timestamp": item.get("timestamp", "")
                }
                validated_history.append(validated_item)
            except Exception as item_error:
                print(f"Warning: Skipping invalid history item: {item_error}")
                continue
        return validated_history
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_history endpoint: {error_details}")
        # Return empty list instead of raising error to prevent UI crashes
        # The frontend can handle empty history gracefully
        return []


@app.delete("/history/{query_id}")
async def delete_history_item(query_id: str, user_id: str = "default_user"):
    """
    Delete a specific query from history.
    
    Only allows deletion if the query belongs to the specified user_id.
    
    Args:
        query_id: Document ID of the query to delete
        user_id: User ID (for verification - must match query owner)
    
    Returns:
        Success message
    """
    # Validate and sanitize user_id
    import re
    if not user_id or not isinstance(user_id, str):
        user_id = "default_user"
    user_id = re.sub(r'[^a-zA-Z0-9_-]', '', user_id)
    if not user_id:
        user_id = "default_user"
    
    try:
        # This verifies the query belongs to the user before deleting
        success = delete_query(query_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Query not found or access denied")
        return {"success": True, "message": "Query deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete query: {str(e)}")


@app.delete("/history")
async def delete_all_history_endpoint(user_id: str = "default_user"):
    """
    Delete all query history for a user.
    
    Only deletes history for the specified user_id.
    
    Args:
        user_id: User ID (must be valid, sanitized)
    
    Returns:
        Number of queries deleted (only for the specified user)
    """
    # Validate and sanitize user_id
    import re
    if not user_id or not isinstance(user_id, str):
        user_id = "default_user"
    user_id = re.sub(r'[^a-zA-Z0-9_-]', '', user_id)
    if not user_id:
        user_id = "default_user"
    
    try:
        # This will only delete history for the specified user_id
        count = delete_all_history(user_id)
        return {"success": True, "deleted_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete history: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

