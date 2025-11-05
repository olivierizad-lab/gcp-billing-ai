#!/usr/bin/env python3
"""
Simple module to query the deployed Agent Engine.

Usage:
    from bq_agent_mick.query_agent import query_agent
    
    response = query_agent("What are the total costs by top 10 services?")
    print(response)

Or run as script:
    python -m bq_agent_mick.query_agent "What are the total costs by top 10 services?"
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

PROJECT_ID = os.getenv("BQ_PROJECT") or os.getenv("GCP_PROJECT_ID", "qwiklabs-asl-04-8e9f23e85ced")
LOCATION = os.getenv("LOCATION", "us-central1")
REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID", "6686143402645389312")


def query_agent(query_text, user_id="default_user"):
    """
    Query the deployed Agent Engine.
    
    Args:
        query_text: The natural language query to send to the agent
        user_id: User ID for the query (optional)
    
    Returns:
        The agent's response text
    """
    try:
        from google.cloud import aiplatform
        from google.cloud.aiplatform.preview import reasoning_engines
        
        # Initialize Vertex AI
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        
        # Get the reasoning engine
        reasoning_engine = reasoning_engines.ReasoningEngine(
            reasoning_engine_name=f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}"
        )
        
        # Query the agent
        print(f"Querying agent: {query_text}")
        print(f"Project: {PROJECT_ID}, Location: {LOCATION}")
        print(f"Reasoning Engine ID: {REASONING_ENGINE_ID}")
        print("-" * 60)
        
        # Use stream_query for streaming responses
        response_text = ""
        for chunk in reasoning_engine.query(
            input={"message": query_text, "user_id": user_id},
            stream=True
        ):
            if hasattr(chunk, 'content'):
                # Extract text from response
                content = chunk.content
                if hasattr(content, 'parts'):
                    for part in content.parts:
                        if hasattr(part, 'text'):
                            text = part.text
                            print(text, end='', flush=True)
                            response_text += text
                elif isinstance(content, str):
                    print(content, end='', flush=True)
                    response_text += content
            elif isinstance(chunk, str):
                print(chunk, end='', flush=True)
                response_text += chunk
        
        print("\n" + "=" * 60)
        return response_text
        
    except ImportError:
        # Fallback to REST API if SDK doesn't support Reasoning Engines directly
        print("Vertex AI SDK Reasoning Engine support not available, using REST API...")
        return _query_via_rest(query_text, user_id)
    except Exception as e:
        print(f"Error querying agent: {e}")
        import traceback
        traceback.print_exc()
        return None


def _query_via_rest(query_text, user_id="default_user"):
    """Fallback to REST API if SDK doesn't work."""
    try:
        from google.auth import default
        from google.auth.transport.requests import Request
        import requests
        
        # Get credentials
        credentials, _ = default()
        if not credentials.valid:
            credentials.refresh(Request())
        
        # Build API endpoint
        base_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1"
        endpoint = f"{base_url}/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}:streamQuery"
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "input": {
                "message": query_text,
                "user_id": user_id
            }
        }
        
        print(f"Querying via REST API...")
        
        # Stream the response
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            stream=True,
            timeout=180
        )
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text[:500])
            return None
        
        # Parse streaming JSON response
        import json
        response_text = ""
        
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
                                    print(text, end='', flush=True)
                                    response_text += text
                except json.JSONDecodeError:
                    # Skip non-JSON lines
                    pass
        
        print("\n" + "=" * 60)
        return response_text
        
    except Exception as e:
        print(f"Error querying via REST API: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Command-line interface."""
    if len(sys.argv) < 2:
        print("Usage: python -m bq_agent_mick.query_agent 'Your question here'")
        print("\nOr use as a module:")
        print("  from bq_agent_mick.query_agent import query_agent")
        print("  response = query_agent('Your question')")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    response = query_agent(query)
    
    if response:
        print("\n✓ Query completed successfully")
    else:
        print("\n✗ Query failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
