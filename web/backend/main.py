#!/usr/bin/env python3
"""
FastAPI backend server for the Agent Engine chat interface.

This server provides REST API endpoints for querying deployed Vertex AI Agent Engine agents.
It handles authentication and streams responses back to the frontend.
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import google.auth
from google.auth.transport.requests import Request
import requests
from history import save_query, get_query_history, delete_query, delete_all_history
from auth import (
    create_user, authenticate_user, get_user_by_id, delete_user,
    create_access_token, decode_token, validate_email_domain, REQUIRED_DOMAIN
)

# Load environment variables (optional - for local development only)
# In Cloud Run/Docker, all configuration comes from environment variables
# This .env file loading is optional and only used for local development
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file, override=False)
# If .env doesn't exist (Cloud Run), that's fine - use environment variables

app = FastAPI(title="Agent Engine Chat API", version="1.0.0")

# CORS configuration - allow React frontend
# For Cloud Run, allow origins from environment variable or default to localhost
allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Default to localhost for local development
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

# Always allow the UI service origin if we can detect it
ui_origin = "https://agent-engine-ui-jgvhuxsatq-uc.a.run.app"
if ui_origin not in allowed_origins:
    allowed_origins.append(ui_origin)

# Add CORS middleware - must be added before other middleware
# This ensures CORS headers are included in ALL responses, including errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# JWT Bearer token security
security = HTTPBearer()

# Authentication dependency
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token from Authorization header."""
    token = credentials.credentials
    
    # Decode and verify the token
    decoded_token = decode_token(token)
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Get user to verify they're still active
    user = get_user_by_id(decoded_token.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return decoded_token

# Configuration
PROJECT_ID = os.getenv("BQ_PROJECT") or os.getenv("GCP_PROJECT_ID", "qwiklabs-asl-04-8e9f23e85ced")
LOCATION = os.getenv("LOCATION", "us-central1")

# Cache for agent configurations (to avoid API calls on every request)
_agent_configs_cache: Optional[Dict] = None
_agent_configs_cache_time: float = 0
AGENT_CONFIGS_CACHE_TTL = 300  # Cache for 5 minutes


def scan_agent_engine_reasoning_engines(project_id: str, location: str) -> Dict:
    """Scan Vertex AI Agent Engine for all deployed reasoning engines."""
    configs = {}
    
    try:
        # Use Google Auth to get credentials
        credentials, _ = google.auth.default()
        if not credentials.valid:
            credentials.refresh(Request())
        
        # Build API endpoint
        base_url = f"https://{location}-aiplatform.googleapis.com/v1"
        endpoint = f"{base_url}/projects/{project_id}/locations/{location}/reasoningEngines"
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }
        
        # Make API call
        response = requests.get(endpoint, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            engines = data.get('reasoningEngines', [])
            
            # Convert reasoning engines to agent configs
            for engine in engines:
                display_name = engine.get('displayName', '')
                name = engine.get('name', '')
                description = engine.get('description', '')
                
                # Extract reasoning engine ID from name (format: projects/.../locations/.../reasoningEngines/ID)
                engine_id = name.split('/')[-1] if '/' in name else name
                
                # Create a sanitized key from display name (lowercase, replace spaces with underscores)
                # Fallback to engine_id if display_name is empty
                key = display_name.lower().replace(' ', '_').replace('-', '_') if display_name else f"agent_{engine_id}"
                # Remove special characters
                key = ''.join(c for c in key if c.isalnum() or c == '_')
                # Ensure it's not empty
                if not key:
                    key = f"agent_{engine_id}"
                
                configs[key] = {
                    "name": key,
                    "display_name": display_name or f"Agent {engine_id}",
                    "description": description or "Vertex AI Agent Engine agent",
                    "reasoning_engine_id": engine_id,
                }
            
            print(f"✓ Scanned Agent Engine: Found {len(configs)} reasoning engine(s)")
        else:
            print(f"⚠ Failed to scan Agent Engine: HTTP {response.status_code}")
            if response.status_code == 403:
                print("  Permission denied - check IAM permissions for Vertex AI API")
            elif response.status_code == 404:
                print("  API endpoint not found - check location and project ID")
    
    except Exception as e:
        print(f"⚠ Error scanning Agent Engine: {e}")
        print("  No agents will be available until the API is accessible")
    
    return configs

def load_agent_configs(force_refresh: bool = False) -> Dict:
    """
    Load agent configurations by scanning Agent Engine for all deployed reasoning engines.
    
    Uses caching to avoid API calls on every request. Cache TTL is 5 minutes.
    Returns empty dict if no agents are found or if scanning fails.
    """
    global _agent_configs_cache, _agent_configs_cache_time
    
    current_time = time.time()
    
    # Check cache
    if not force_refresh and _agent_configs_cache is not None:
        if current_time - _agent_configs_cache_time < AGENT_CONFIGS_CACHE_TTL:
            return _agent_configs_cache
    
    # Scan Agent Engine for all reasoning engines
    scanned_configs = scan_agent_engine_reasoning_engines(PROJECT_ID, LOCATION)
    
    # Update cache
    _agent_configs_cache = scanned_configs
    _agent_configs_cache_time = current_time
    
    if scanned_configs:
        print(f"✓ Loaded {len(scanned_configs)} agent(s) from Agent Engine")
    else:
        print("⚠ No agents found in Agent Engine")
    
    return scanned_configs

# Load initial agent configs
AGENT_CONFIGS = load_agent_configs()


# Authentication models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    created_at: Optional[str] = None

class QueryRequest(BaseModel):
    message: str
    agent_name: str
    session_id: Optional[str] = None  # Session ID for conversation context
    # Note: user_id is removed - we use the authenticated user's ID from the token


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


def query_agent_stream(agent_name: str, message: str, user_id: str):
    """
    Stream query to the agent via Vertex AI REST API.
    
    Yields chunks of the response as they arrive.
    """
    # Get agent configuration (use cached configs)
    configs = load_agent_configs()
    if agent_name not in configs:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    agent_config = configs[agent_name]
    reasoning_engine_id = agent_config["reasoning_engine_id"]
    
    if not reasoning_engine_id:
        raise HTTPException(
            status_code=400,
            detail=f"Agent '{agent_name}' is not configured. Please deploy the agent to Vertex AI Agent Engine."
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


def query_agent_stream_with_save(agent_name: str, message: str, user_id: str, session_id: Optional[str] = None):
    """
    Stream query to agent and save to Firestore after completion.
    
    Yields chunks of the response and saves the complete query/response after streaming.
    
    Args:
        agent_name: Name of the agent
        message: User's message
        user_id: User ID
        session_id: Optional session ID for conversation context (if None, Agent Engine creates new session)
    """
    response_text = ""
    
    try:
        # Get agent configuration (use cached configs)
        configs = load_agent_configs()
        if agent_name not in configs:
            error_msg = f'Agent \'{agent_name}\' not found'
            yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"
            return
        
        agent_config = configs[agent_name]
        reasoning_engine_id = agent_config["reasoning_engine_id"]
        
        if not reasoning_engine_id:
            error_msg = f'Agent \'{agent_name}\' is not configured. Please deploy the agent to Vertex AI Agent Engine.'
            yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"
            return
        
        # Get credentials
        try:
            credentials = get_credentials()
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Failed to get credentials: {str(e)}', 'done': True})}\n\n"
            return
        
        # Build API endpoint - include session_id if provided for conversation context
        base_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1"
        
        # Build payload - match the format used in interactive.py
        # Note: Agent Engine REST API may not support session_id in request body
        # Session management might be handled differently via the API
        payload = {
            "input": {
                "message": message,
                "user_id": user_id
            }
        }
        
        # Log the payload for debugging
        print(f"DEBUG: Request payload: {json.dumps(payload, indent=2)}")
        
        # Agent Engine REST API endpoint - sessions are managed automatically or via request body
        # Note: The REST API doesn't use sessions in the URL path like ADK directly
        endpoint = f"{base_url}/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{reasoning_engine_id}:streamQuery"
        
        if session_id:
            print(f"Session ID provided: {session_id} (may be used for context in request body)")
        else:
            print("No session_id provided - Agent Engine will create/manage sessions automatically")
        
        # Log the endpoint being called for debugging
        print(f"DEBUG: Calling Agent Engine endpoint:")
        print(f"  Project: {PROJECT_ID}")
        print(f"  Location: {LOCATION}")
        print(f"  Reasoning Engine ID: {reasoning_engine_id}")
        print(f"  Endpoint: {endpoint}")
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }
        
        # Stream the response
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                stream=True,
                timeout=180
            )
            
            if response.status_code != 200:
                error_text = response.text[:500]
                print(f"ERROR: Agent Engine returned HTTP {response.status_code}")
                print(f"Error response: {error_text}")
                print(f"Endpoint used: {endpoint}")
                yield f"data: {json.dumps({'error': f'Agent query failed (HTTP {response.status_code}): {error_text}', 'done': True})}\n\n"
                return
            
            # Parse streaming JSON response and collect text
            try:
                print(f"DEBUG: Response status: {response.status_code}")
                print(f"DEBUG: Response headers: {dict(response.headers)}")
                print(f"DEBUG: Response content-type: {response.headers.get('content-type', 'N/A')}")
                
                line_count = 0
                chunk_count = 0
                
                # Try different methods to read the stream
                # Method 1: iter_lines (for newline-delimited JSON)
                for line in response.iter_lines(decode_unicode=True):
                    chunk_count += 1
                    if line:
                        line_count += 1
                        print(f"DEBUG: Raw line {line_count}: {line[:200]}")
                        try:
                            data = json.loads(line)
                            
                            # Log first few lines for debugging (full structure)
                            if line_count <= 5:
                                print(f"DEBUG: Response line {line_count} full structure:")
                                print(json.dumps(data, indent=2)[:1000])
                                print("-" * 80)
                            
                            # Extract text from response - handle different response formats
                            # Format 1: content.parts[].text
                            content = data.get("content", {})
                            if isinstance(content, dict):
                                parts = content.get("parts", [])
                                if parts:
                                    print(f"DEBUG: Found {len(parts)} parts in content")
                                for i, part in enumerate(parts):
                                    if isinstance(part, dict):
                                        print(f"DEBUG: Part {i} keys: {list(part.keys())}")
                                        text = part.get("text")
                                        if text:
                                            print(f"DEBUG: Found text in part {i}: {text[:100]}...")
                                            response_text += text
                                            # Yield as Server-Sent Events format
                                            yield f"data: {json.dumps({'text': text})}\n\n"
                                        else:
                                            print(f"DEBUG: Part {i} has no 'text' key, keys are: {list(part.keys())}")
                            
                            # Format 2: Check for candidates (Gemini API format)
                            candidates = data.get("candidates", [])
                            if candidates:
                                print(f"DEBUG: Found {len(candidates)} candidates")
                                for i, candidate in enumerate(candidates):
                                    candidate_content = candidate.get("content", {})
                                    if isinstance(candidate_content, dict):
                                        candidate_parts = candidate_content.get("parts", [])
                                        for j, part in enumerate(candidate_parts):
                                            if isinstance(part, dict):
                                                text = part.get("text")
                                                if text:
                                                    print(f"DEBUG: Found text in candidate {i}, part {j}: {text[:100]}...")
                                                    response_text += text
                                                    yield f"data: {json.dumps({'text': text})}\n\n"
                            
                            # Format 3: Direct text field
                            if "text" in data:
                                text = data["text"]
                                if text:
                                    print(f"DEBUG: Found direct text field: {text[:100]}...")
                                    response_text += text
                                    yield f"data: {json.dumps({'text': text})}\n\n"
                                    
                        except json.JSONDecodeError as json_err:
                            # Skip non-JSON lines but log for debugging
                            print(f"Warning: Skipping non-JSON line: {line[:100]}")
                            continue
                        except Exception as parse_err:
                            print(f"Warning: Error parsing line: {parse_err}")
                            import traceback
                            traceback.print_exc()
                            continue
                
                print(f"DEBUG: Processed {line_count} non-empty lines from {chunk_count} total chunks")
                print(f"DEBUG: Total response text length: {len(response_text)}")
                
                # If no lines were found, try reading the raw response
                if line_count == 0 and chunk_count == 0:
                    print("DEBUG: No lines found in stream, trying raw response...")
                    try:
                        raw_content = response.text
                        print(f"DEBUG: Raw response content length: {len(raw_content)}")
                        print(f"DEBUG: Raw response (first 500 chars): {raw_content[:500]}")
                        
                        # Try to parse as JSON
                        try:
                            data = json.loads(raw_content)
                            print(f"DEBUG: Parsed as single JSON object")
                            print(f"DEBUG: JSON keys: {list(data.keys())}")
                            
                            # Extract text from the JSON
                            content = data.get("content", {})
                            if isinstance(content, dict):
                                parts = content.get("parts", [])
                                for part in parts:
                                    if isinstance(part, dict):
                                        text = part.get("text")
                                        if text:
                                            response_text += text
                                            yield f"data: {json.dumps({'text': text})}\n\n"
                        except json.JSONDecodeError:
                            print("DEBUG: Response is not JSON, might be text or other format")
                            if raw_content:
                                response_text = raw_content
                                yield f"data: {json.dumps({'text': raw_content})}\n\n"
                    except Exception as raw_err:
                        print(f"DEBUG: Error reading raw response: {raw_err}")
                
                if line_count > 0 and not response_text:
                    print(f"WARNING: Received {line_count} lines but extracted no text content!")
                    print(f"Check the DEBUG logs above to see the response structure")
            except Exception as stream_err:
                print(f"Error during streaming: {stream_err}")
                import traceback
                traceback.print_exc()
                # If we have partial response, continue to save it
                if not response_text:
                    yield f"data: {json.dumps({'error': f'Stream error: {str(stream_err)}', 'done': True})}\n\n"
                    return
            
            # Save to Firestore after streaming completes
            if response_text:
                try:
                    print(f"Saving query to Firestore: user_id={user_id}, agent={agent_name}, message_length={len(message)}, response_length={len(response_text)}")
                    query_id = save_query(user_id, agent_name, message, response_text)
                    print(f"Successfully saved query with ID: {query_id}")
                    # Send query_id and completion marker
                    yield f"data: {json.dumps({'query_id': query_id, 'done': True})}\n\n"
                except Exception as save_err:
                    # Log error but don't fail the request
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"ERROR: Failed to save query to Firestore: {save_err}")
                    print(f"Traceback: {error_details}")
                    yield f"data: {json.dumps({'done': True, 'save_error': str(save_err)})}\n\n"
            else:
                # No response text, just send done marker
                print("Warning: No response text to save (empty response)")
                yield f"data: {json.dumps({'done': True, 'warning': 'Empty response from agent'})}\n\n"
                
        except requests.exceptions.Timeout:
            yield f"data: {json.dumps({'error': 'Request timeout (180s exceeded)', 'done': True})}\n\n"
            return
        except requests.exceptions.RequestException as req_err:
            yield f"data: {json.dumps({'error': f'Request failed: {str(req_err)}', 'done': True})}\n\n"
            return
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Unexpected error in query_agent_stream_with_save: {e}")
            print(f"Traceback: {error_details}")
            yield f"data: {json.dumps({'error': f'Query failed: {str(e)}', 'done': True})}\n\n"
            return
            
    except Exception as outer_err:
        # Catch any unexpected errors at the outer level
        import traceback
        error_details = traceback.format_exc()
        print(f"Critical error in query_agent_stream_with_save (outer): {outer_err}")
        print(f"Traceback: {error_details}")
        try:
            yield f"data: {json.dumps({'error': f'Critical error: {str(outer_err)}', 'done': True})}\n\n"
        except:
            # If we can't even yield, the stream is broken
            print("Fatal: Cannot yield error message, stream is broken")
            pass


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Agent Engine Chat API",
        "version": "1.0.0",
        "agents": list(AGENT_CONFIGS.keys())
    }


# Authentication endpoints
@app.post("/auth/signup", response_model=UserResponse)
async def signup(request: SignupRequest):
    """Create a new user account."""
    try:
        user = create_user(request.email, request.password)
        return UserResponse(**user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")


@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login and get access token."""
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["user_id"], "email": user["email"]}
    )
    
    return TokenResponse(
        access_token=access_token,
        user_id=user["user_id"],
        email=user["email"]
    )


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(user_token: dict = Depends(verify_token)):
    """Get current user information."""
    user = get_user_by_id(user_token.get("user_id"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**user)


@app.delete("/auth/me")
async def delete_current_user(user_token: dict = Depends(verify_token)):
    """Delete current user account."""
    user_id = user_token.get("user_id")
    success = delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "message": "Account deleted"}


@app.get("/agents", response_model=List[AgentInfo])
async def list_agents(force_refresh: bool = False):
    """
    List all available agents from Vertex AI Agent Engine.
    
    Automatically scans all deployed reasoning engines. Results are cached for 5 minutes.
    Use ?force_refresh=true to force a fresh scan.
    """
    # Note: Agents list is public (no auth required) - agent info is not sensitive
    # This allows the frontend to load agents before authentication
    
    # Refresh agent configs if requested or cache expired
    configs = load_agent_configs(force_refresh=force_refresh)
    
    agents = []
    for agent_name, config in configs.items():
        agents.append(AgentInfo(
            name=config["name"],
            display_name=config["display_name"],
            description=config["description"],
            reasoning_engine_id=config["reasoning_engine_id"],
            is_available=bool(config["reasoning_engine_id"])
        ))
    
    # Sort by display name for consistent ordering
    agents.sort(key=lambda x: x.display_name)
    
    return agents


@app.post("/query/stream")
async def query_stream(request: QueryRequest, user_token: dict = Depends(verify_token)):
    """
    Stream query to an agent and save to Firestore.
    
    Returns a Server-Sent Events (SSE) stream of response chunks.
    Query is automatically saved to Firestore after completion.
    
    If session_id is provided, the agent will maintain conversation context.
    
    IMPORTANT: Uses the authenticated user's ID from the token, not from the request.
    This ensures users can only save queries under their own account.
    """
    # Get user_id from the authenticated token (security: don't trust client)
    authenticated_user_id = user_token.get("user_id")
    if not authenticated_user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    
    return StreamingResponse(
        query_agent_stream_with_save(
            request.agent_name, 
            request.message, 
            authenticated_user_id,  # Use authenticated user's ID
            request.session_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, user_token: dict = Depends(verify_token)):
    """
    Query an agent (non-streaming, returns complete response).
    
    Use /query/stream for streaming responses.
    
    IMPORTANT: Uses the authenticated user's ID from the token, not from the request.
    """
    # Get user_id from the authenticated token (security: don't trust client)
    authenticated_user_id = user_token.get("user_id")
    if not authenticated_user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    
    response_text = ""
    query_id = None
    try:
        for chunk in query_agent_stream_with_save(request.agent_name, request.message, authenticated_user_id):
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
        user_id=authenticated_user_id,  # Use authenticated user's ID
        query_id=query_id
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "project_id": PROJECT_ID, "location": LOCATION}


@app.get("/debug/agents")
async def debug_agents():
    """Debug endpoint to check agent configurations."""
    debug_info = {
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "agents": {}
    }
    
    # Get current agent configs (may be cached)
    configs = load_agent_configs()
    for agent_name, config in configs.items():
        reasoning_engine_id = config["reasoning_engine_id"]
        endpoint_base = f"https://{LOCATION}-aiplatform.googleapis.com/v1"
        endpoint = f"{endpoint_base}/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{reasoning_engine_id}:streamQuery"
        
        debug_info["agents"][agent_name] = {
            "display_name": config["display_name"],
            "reasoning_engine_id": reasoning_engine_id,
            "is_configured": bool(reasoning_engine_id),
            "endpoint": endpoint if reasoning_engine_id else None
        }
    
    return debug_info


@app.get("/history")
async def get_history(user_id: str, limit: int = 50, user_token: dict = Depends(verify_token)):
    """
    Get query history for a user.
    
    Only returns history for the authenticated user.
    
    Args:
        user_id: User ID (must match authenticated user's user_id)
        limit: Maximum number of queries to return (default: 50, max: 100)
    
    Returns:
        List of query history items (only for the authenticated user)
    """
    # Verify user_id matches authenticated user
    if user_id != user_token.get("user_id"):
        raise HTTPException(status_code=403, detail="Cannot access other users' history")
    
    # Validate and sanitize user_id
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(status_code=400, detail="Invalid user_id")
    
    # Sanitize: only allow alphanumeric, underscore, hyphen
    import re
    user_id = re.sub(r'[^a-zA-Z0-9_-]', '', user_id)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user_id")
    
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
async def delete_history_item(query_id: str, user_id: str, user_token: dict = Depends(verify_token)):
    """
    Delete a specific query from history.
    
    Only allows deletion if the query belongs to the authenticated user.
    
    Args:
        query_id: Document ID of the query to delete
        user_id: User ID (must match authenticated user's user_id)
    
    Returns:
        Success message
    """
    # Verify user_id matches authenticated user
    if user_id != user_token.get("user_id"):
        raise HTTPException(status_code=403, detail="Cannot delete other users' queries")
    
    # Validate and sanitize user_id
    import re
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(status_code=400, detail="Invalid user_id")
    user_id = re.sub(r'[^a-zA-Z0-9_-]', '', user_id)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user_id")
    
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
async def delete_all_history_endpoint(user_id: str, user_token: dict = Depends(verify_token)):
    """
    Delete all query history for the authenticated user.
    
    Args:
        user_id: User ID (must match authenticated user's user_id)
    
    Returns:
        Number of queries deleted (only for the authenticated user)
    """
    # Verify user_id matches authenticated user
    if user_id != user_token.get("user_id"):
        raise HTTPException(status_code=403, detail="Cannot delete other users' history")
    
    # Validate and sanitize user_id
    import re
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(status_code=400, detail="Invalid user_id")
    user_id = re.sub(r'[^a-zA-Z0-9_-]', '', user_id)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user_id")
    
    try:
        # This will only delete history for the specified user_id
        count = delete_all_history(user_id)
        return {"success": True, "deleted_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete history: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

