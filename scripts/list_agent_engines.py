#!/usr/bin/env python3
"""
List all Agent Engine deployments for a project.

Usage:
    python scripts/list_agent_engines.py [--project PROJECT_ID] [--location LOCATION] [--filter-name NAME]
"""
import argparse
import sys
from datetime import datetime
from google.cloud import aiplatform

def list_reasoning_engines(project_id, location, filter_name=None):
    """List all reasoning engines in the project."""
    aiplatform.init(project=project_id, location=location)
    
    try:
        from google.cloud.aiplatform.preview import reasoning_engines
        
        print(f"Listing Reasoning Engines in project: {project_id}")
        print(f"Location: {location}")
        print(f"{'='*80}")
        
        # List all reasoning engines
        all_engines = []
        try:
            engines = reasoning_engines.ReasoningEngine.list()
            for engine in engines:
                all_engines.append(engine)
        except Exception as e:
            print(f"Error listing engines: {e}")
            print("\nTrying alternative method via REST API...")
            return list_via_api(project_id, location, filter_name)
        
        # Filter by name if provided
        if filter_name:
            all_engines = [e for e in all_engines if filter_name.lower() in e.display_name.lower()]
        
        # Sort by creation time (newest first)
        all_engines.sort(key=lambda x: x.create_time if hasattr(x, 'create_time') else datetime.min, reverse=True)
        
        print(f"\nFound {len(all_engines)} reasoning engine(s):\n")
        
        for i, engine in enumerate(all_engines, 1):
            display_name = getattr(engine, 'display_name', 'N/A')
            name = getattr(engine, 'name', 'N/A')
            create_time = getattr(engine, 'create_time', None)
            description = getattr(engine, 'description', 'N/A')
            
            # Extract reasoning engine ID from name
            engine_id = name.split('/')[-1] if '/' in name else name
            
            print(f"{i}. {display_name}")
            print(f"   ID: {engine_id}")
            print(f"   Created: {create_time}")
            print(f"   Description: {description}")
            print()
        
        if all_engines:
            latest = all_engines[0]
            latest_id = latest.name.split('/')[-1] if '/' in latest.name else latest.name
            print(f"{'='*80}")
            print(f"✓ Latest deployment: {latest.display_name}")
            print(f"  Reasoning Engine ID: {latest_id}")
            print(f"\nTo use this deployment, update your .env file:")
            print(f"  REASONING_ENGINE_ID={latest_id}")
        
    except ImportError:
        print("Reasoning Engine preview API not available, using REST API...")
        return list_via_api(project_id, location, filter_name)
    except Exception as e:
        print(f"Error: {e}")
        print("Falling back to REST API...")
        return list_via_api(project_id, location, filter_name)

def list_via_api(project_id, location, filter_name=None):
    """List using Vertex AI REST API directly."""
    try:
        from google.auth import default
        from google.auth.transport.requests import Request
        import requests
        
        # Get credentials
        credentials, _ = default()
        if not credentials.valid:
            credentials.refresh(Request())
        
        # Build API endpoint
        base_url = f"https://{location}-aiplatform.googleapis.com/v1"
        endpoint = f"{base_url}/projects/{project_id}/locations/{location}/reasoningEngines"
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }
        
        print("Fetching deployments from Vertex AI API...")
        
        response = requests.get(endpoint, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text[:500])
            print("\nPlease check the console manually:")
            print(f"https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={project_id}")
            return
        
        data = response.json()
        engines = data.get('reasoningEngines', [])
        
        if filter_name:
            engines = [e for e in engines if filter_name.lower() in e.get('displayName', '').lower()]
        
        # Sort by createTime
        engines.sort(key=lambda x: x.get('createTime', ''), reverse=True)
        
        print(f"\nFound {len(engines)} reasoning engine(s):\n")
        
        for i, engine in enumerate(engines, 1):
            display_name = engine.get('displayName', 'N/A')
            name = engine.get('name', 'N/A')
            create_time = engine.get('createTime', 'N/A')
            
            # Extract ID
            engine_id = name.split('/')[-1] if '/' in name else name
            
            print(f"{i}. {display_name}")
            print(f"   ID: {engine_id}")
            print(f"   Created: {create_time}")
            print()
        
        if engines:
            latest = engines[0]
            latest_id = latest['name'].split('/')[-1]
            print(f"{'='*80}")
            print(f"✓ Latest deployment: {latest.get('displayName', 'N/A')}")
            print(f"  Reasoning Engine ID: {latest_id}")
            print(f"\nTo use this deployment, update your .env file:")
            print(f"  REASONING_ENGINE_ID={latest_id}")
        else:
            print("No deployments found.")
            if filter_name:
                print(f"(Filtered by name: {filter_name})")
    
    except ImportError:
        print("Error: 'requests' library not available")
        print("Install with: pip install requests")
        print("\nPlease check the console manually:")
        print(f"https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={project_id}")
    except Exception as e:
        print(f"Error using API: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease check the console manually:")
        print(f"https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={project_id}")

def main():
    parser = argparse.ArgumentParser(description="List Agent Engine deployments")
    parser.add_argument("--project", help="GCP project ID", default=None)
    parser.add_argument("--location", default="us-central1", help="GCP location")
    parser.add_argument("--filter-name", help="Filter by agent name (e.g., bq_agent_mick)")
    
    args = parser.parse_args()
    
    # Get project ID
    project_id = args.project
    if not project_id:
        import subprocess
        try:
            result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True,
                text=True,
                check=True
            )
            project_id = result.stdout.strip()
        except Exception:
            print("Error: PROJECT_ID must be set")
            print("  Set it with: --project PROJECT_ID")
            print("  Or: gcloud config set project PROJECT_ID")
            sys.exit(1)
    
    list_reasoning_engines(project_id, args.location, args.filter_name)

if __name__ == "__main__":
    main()
