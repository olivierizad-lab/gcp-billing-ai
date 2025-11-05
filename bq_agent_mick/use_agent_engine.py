#!/usr/bin/env python3
"""
Example script to use the deployed bq_agent_mick Agent Engine.

Usage:
    python use_agent_engine.py "What are the top 10 services by cost?"
"""

import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def query_agent_engine(project_id, location, agent_engine_id, query_text):
    """
    Query the deployed Agent Engine agent.
    
    Args:
        project_id: GCP project ID
        location: Vertex AI location (e.g., us-central1)
        agent_engine_id: The Reasoning Engine ID from deployment
        query_text: The question/query to send to the agent
    """
    try:
        from google.cloud import aiplatform
        from google.cloud.aiplatform import base
        from google.cloud.aiplatform.preview import reasoning_engines
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        print(f"Connecting to Reasoning Engine: {agent_engine_id}")
        
        # Get the reasoning engine resource name
        reasoning_engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{agent_engine_id}"
        
        print(f"Sending query: {query_text}")
        print("-" * 60)
        
        # Query the reasoning engine using the REST API approach
        # Agent Engine uses REST API for querying
        try:
            # Try using the reasoning engines client
            client = aiplatform.gapic.ReasoningEngineServiceClient()
            
            # Query the reasoning engine
            request = aiplatform.gapic.QueryReasoningEngineRequest(
                name=reasoning_engine_name,
                input={"query": query_text}
            )
            
            response = client.query_reasoning_engine(request=request)
            
            print("\nAgent Response:")
            print("=" * 60)
            print(response.output if hasattr(response, 'output') else response)
            print("=" * 60)
            
            return response
            
        except Exception as api_error:
            # Fallback: Try using REST API directly
            print(f"⚠ API client method failed: {api_error}")
            print("Trying REST API fallback...")
            
            from google.auth import default
            from google.auth.transport.requests import Request
            import requests
            
            credentials, _ = default()
            if not credentials.valid:
                credentials.refresh(Request())
            
            url = f"https://{location}-aiplatform.googleapis.com/v1/{reasoning_engine_name}:query"
            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
            }
            payload = {
                "input": {
                    "query": query_text
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            output = result.get("output", result)
            
            print("\nAgent Response:")
            print("=" * 60)
            print(output)
            print("=" * 60)
            
            return output
        
    except ImportError as import_err:
        print(f"Error: Missing dependency - {import_err}")
        print("Install with: pip install google-cloud-aiplatform requests")
        return None
    except Exception as e:
        print(f"Error querying agent: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Query the deployed bq_agent_mick Agent Engine"
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="The question to ask the agent"
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("BQ_PROJECT"),
        help="GCP Project ID"
    )
    parser.add_argument(
        "--location",
        default="us-central1",
        help="Vertex AI location (default: us-central1)"
    )
    parser.add_argument(
        "--agent-engine-id",
        default=None,
        help="Agent Engine ID (Reasoning Engine ID). If not provided, will try to find from recent deployments."
    )
    
    args = parser.parse_args()
    
    # Validate project ID
    if not args.project:
        print("Error: Project ID required.")
        print("Set GCP_PROJECT_ID, GOOGLE_CLOUD_PROJECT, or BQ_PROJECT environment variable")
        print("Or use --project argument")
        return
    
    # Get query text
    if args.query:
        query_text = args.query
    else:
        # Interactive mode
        print("Enter your query (or 'exit' to quit):")
        query_text = input("> ")
        if query_text.lower() in ['exit', 'quit']:
            return
    
    # Get agent engine ID
    agent_engine_id = args.agent_engine_id
    if not agent_engine_id:
        print("⚠ Agent Engine ID not provided.")
        print("You can find it from:")
        print("  1. The deployment output (Reasoning Engine ID)")
        print("  2. The Console URL (in the resource name)")
        print("  3. Recent deployments: 6060143054440890368")
        print()
        use_default = input("Use recent ID (6060143054440890368)? [Y/n]: ").strip().lower()
        if use_default in ['', 'y', 'yes']:
            agent_engine_id = "6060143054440890368"
        else:
            agent_engine_id = input("Enter Agent Engine ID: ").strip()
    
    if not agent_engine_id:
        print("Error: Agent Engine ID required")
        return
    
    # Query the agent
    query_agent_engine(args.project, args.location, agent_engine_id, query_text)


if __name__ == "__main__":
    main()
