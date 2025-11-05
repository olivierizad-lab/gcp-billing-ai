#!/usr/bin/env python3
"""
Inspect a Reasoning Engine deployment to see what might be holding onto it.

This script helps debug why deployments can't be deleted by checking:
- Deployment details
- Potential active operations
- API endpoints that might reveal session information

Usage:
    python scripts/inspect_deployment.py --engine-id <REASONING_ENGINE_ID>
"""
import argparse
import sys
from google.auth import default
from google.auth.transport.requests import Request
import requests
import json
from datetime import datetime

def inspect_deployment(project_id, location, engine_id):
    """Inspect a deployment to see what might be holding onto it."""
    print(f"\n{'='*80}")
    print(f"Inspecting Reasoning Engine: {engine_id}")
    print(f"Project: {project_id}, Location: {location}")
    print(f"{'='*80}\n")
    
    credentials, _ = default()
    if not credentials.valid:
        credentials.refresh(Request())
    
    base_url = f"https://{location}-aiplatform.googleapis.com/v1"
    engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}"
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }
    
    # 1. Get deployment details
    print("1. Deployment Details")
    print("-" * 80)
    try:
        endpoint = f"{base_url}/{engine_name}"
        response = requests.get(endpoint, headers=headers, timeout=10)
        
        if response.status_code == 200:
            engine = response.json()
            print(f"   Display Name: {engine.get('displayName', 'N/A')}")
            print(f"   Created: {engine.get('createTime', 'N/A')}")
            print(f"   Updated: {engine.get('updateTime', 'N/A')}")
            print(f"   State: {engine.get('state', 'N/A')}")
            
            # Calculate age
            if 'createTime' in engine:
                try:
                    created = datetime.fromisoformat(engine['createTime'].replace('Z', '+00:00'))
                    now = datetime.now(created.tzinfo)
                    age = now - created
                    print(f"   Age: {age.days} days, {age.seconds // 3600} hours")
                except:
                    pass
            
            # Check for any fields that might indicate active sessions
            print(f"\n   Available fields: {', '.join(engine.keys())}")
            
            # Look for any session-related or operation-related fields
            for key, value in engine.items():
                if any(term in key.lower() for term in ['session', 'operation', 'state', 'status']):
                    print(f"   {key}: {str(value)[:100]}")
        else:
            print(f"   ✗ Failed to get deployment: HTTP {response.status_code}")
            print(f"   {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 2. Check for active operations
    print("\n2. Checking for Active Operations")
    print("-" * 80)
    try:
        # Check operations API
        ops_endpoint = f"{base_url}/projects/{project_id}/locations/{location}/operations"
        params = {"filter": f'name:"{engine_name}"'}
        response = requests.get(ops_endpoint, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            ops_data = response.json()
            operations = ops_data.get('operations', [])
            active_ops = [op for op in operations if not op.get('done', True)]
            print(f"   Found {len(operations)} total operations")
            print(f"   Active operations: {len(active_ops)}")
            
            if active_ops:
                print("\n   Active operations:")
                for op in active_ops[:5]:  # Show first 5
                    op_name = op.get('name', 'N/A')
                    print(f"     - {op_name.split('/')[-1]}")
            elif operations:
                print("\n   Recent completed operations:")
                for op in operations[:3]:  # Show first 3
                    op_name = op.get('name', 'N/A')
                    done = op.get('done', False)
                    print(f"     - {op_name.split('/')[-1]} (done: {done})")
        else:
            print(f"   Could not check operations: HTTP {response.status_code}")
    except Exception as e:
        print(f"   Error checking operations: {e}")
    
    # 3. Try to get more details via error message
    print("\n3. Attempting Delete (to get detailed error)")
    print("-" * 80)
    try:
        endpoint = f"{base_url}/{engine_name}"
        response = requests.delete(endpoint, headers=headers, timeout=10)
        
        if response.status_code in [200, 204]:
            print("   ✓ Delete successful (unexpected!)")
        elif response.status_code == 400:
            error_data = response.json()
            error_obj = error_data.get('error', {})
            error_msg = error_obj.get('message', '')
            print(f"   Error message: {error_msg}")
            
            # Try to extract more details
            details = error_obj.get('details', [])
            if details:
                print(f"\n   Error details:")
                for detail in details:
                    if isinstance(detail, dict):
                        print(f"     {json.dumps(detail, indent=6)}")
        else:
            print(f"   HTTP {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Check logs suggestion
    print("\n4. Recommendations")
    print("-" * 80)
    print("   To investigate further:")
    print(f"   1. Check Google Cloud Logs:")
    print(f"      https://console.cloud.google.com/logs/query?project={project_id}")
    print(f"      Filter by: resource.type=\"reasoning_engine\" AND resource.labels.reasoning_engine_id=\"{engine_id}\"")
    print()
    print(f"   2. Check Agent Engine Console:")
    print(f"      https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={project_id}")
    print(f"      Look for the deployment and check for session/activity indicators")
    print()
    print("   3. Sessions typically expire after 30-60 minutes of inactivity")
    print("      If these are old deployments, sessions may be stuck/stale")
    print()
    print("   4. Try deleting via Console (may have force-delete options)")
    
    print(f"\n{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Inspect a Reasoning Engine deployment to see what's holding onto it"
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
        help="Reasoning Engine ID to inspect"
    )
    
    args = parser.parse_args()
    inspect_deployment(args.project_id, args.location, args.engine_id)

if __name__ == "__main__":
    main()
