#!/usr/bin/env python3
"""
Utility to manage sessions for Vertex AI Reasoning Engines.

Since Vertex AI Reasoning Engines manage sessions internally, this script
explores available options and provides guidance on session management.

Usage:
    python scripts/manage_sessions.py --engine-id <REASONING_ENGINE_ID> --list
    python scripts/manage_sessions.py --engine-id <REASONING_ENGINE_ID> --force-delete
"""
import argparse
import sys
from google.auth import default
from google.auth.transport.requests import Request
import requests
import json

def get_credentials():
    """Get authentication credentials."""
    credentials, _ = default()
    if not credentials.valid:
        credentials.refresh(Request())
    return credentials

def explore_sessions_api(project_id, location, engine_id):
    """Explore available API endpoints for session management."""
    print(f"Exploring session management options for Reasoning Engine: {engine_id}")
    print(f"Project: {project_id}, Location: {location}")
    print("=" * 80)
    
    credentials = get_credentials()
    base_url = f"https://{location}-aiplatform.googleapis.com/v1"
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }
    
    engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}"
    
    # Try to get engine details first
    print("\n1. Getting Reasoning Engine details...")
    endpoint = f"{base_url}/{engine_name}"
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        if response.status_code == 200:
            engine_data = response.json()
            print(f"   ✓ Engine found: {engine_data.get('displayName', 'N/A')}")
            print(f"   Created: {engine_data.get('createTime', 'N/A')}")
            # Check if sessions info is embedded
            if 'sessions' in engine_data:
                print(f"   Found sessions in response: {len(engine_data['sessions'])}")
        else:
            print(f"   ✗ Failed to get engine: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Try various session-related endpoints
    print("\n2. Exploring session management endpoints...")
    
    endpoints_to_try = [
        ("List sessions (standard REST)", f"{base_url}/{engine_name}/sessions"),
        ("List sessions (custom method)", f"{base_url}/{engine_name}:listSessions"),
        ("Get session info", f"{base_url}/{engine_name}:getSessions"),
    ]
    
    for name, endpoint in endpoints_to_try:
        print(f"\n   Trying: {name}")
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            print(f"      Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"      ✓ Success! Response keys: {list(data.keys())[:10]}")
                if 'sessions' in data:
                    sessions = data['sessions']
                    print(f"      Found {len(sessions)} session(s)")
                    for i, session in enumerate(sessions[:3], 1):
                        print(f"        Session {i}: {session.get('name', 'N/A')[:60]}...")
            elif response.status_code == 404:
                print(f"      ✗ Endpoint not found (404)")
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"      ✗ Bad request (400): {error_msg[:100]}")
            else:
                print(f"      ✗ Error: HTTP {response.status_code}")
        except Exception as e:
            print(f"      ✗ Exception: {e}")
    
    return True

def attempt_force_delete(project_id, location, engine_id):
    """Attempt to force delete a Reasoning Engine (may work if sessions expire)."""
    print(f"\n{'='*80}")
    print("Attempting force delete...")
    print("=" * 80)
    
    credentials = get_credentials()
    base_url = f"https://{location}-aiplatform.googleapis.com/v1"
    engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}"
    endpoint = f"{base_url}/{engine_name}"
    
    headers = {
        "Authorization": f"Bearer {credentials.token}",
    }
    
    # Try standard delete
    print("\nTrying standard DELETE request...")
    try:
        response = requests.delete(endpoint, headers=headers, timeout=60)
        if response.status_code in [200, 204]:
            print("   ✓ Successfully deleted!")
            return True
        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"   ✗ Failed: {error_msg}")
            if 'child resources' in error_msg.lower() or 'sessions' in error_msg.lower():
                print("\n   Note: This engine still has active sessions.")
                print("   Sessions must be terminated before the engine can be deleted.")
        else:
            print(f"   ✗ Failed: HTTP {response.status_code}")
            print(f"   {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    return False

def main():
    parser = argparse.ArgumentParser(
        description="Manage sessions for Vertex AI Reasoning Engines"
    )
    parser.add_argument(
        "--project-id",
        default="qwiklabs-asl-04-8e9f23e85ced",
        help="GCP Project ID"
    )
    parser.add_argument(
        "--location",
        default="us-central1",
        help="GCP Location/Region"
    )
    parser.add_argument(
        "--engine-id",
        required=True,
        help="Reasoning Engine ID"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List sessions (explore API)"
    )
    parser.add_argument(
        "--force-delete",
        action="store_true",
        help="Attempt to force delete the engine"
    )
    
    args = parser.parse_args()
    
    if args.list:
        explore_sessions_api(args.project_id, args.location, args.engine_id)
    elif args.force_delete:
        if not attempt_force_delete(args.project_id, args.location, args.engine_id):
            print("\n" + "=" * 80)
            print("RECOMMENDATIONS:")
            print("=" * 80)
            print("""
1. Wait for sessions to expire (typically 30 minutes to a few hours of inactivity)
2. Delete manually via Google Cloud Console:
   https://console.cloud.google.com/vertex-ai/agents/agent-engines
3. Sessions are managed internally by Vertex AI - there's no public API to 
   terminate them directly at this time

Note: The Reasoning Engine API manages sessions internally and doesn't expose
a public endpoint to list or terminate sessions. This is by design for security
and session management reasons.
            """)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
