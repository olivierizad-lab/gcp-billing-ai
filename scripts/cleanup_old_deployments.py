#!/usr/bin/env python3
"""
Clean up old Agent Engine deployments, keeping only the latest N deployments.

Usage:
    python scripts/cleanup_old_deployments.py --agent-name bq_agent_mick --keep 2
    python scripts/cleanup_old_deployments.py --agent-name bq_agent_mick --keep 1 --dry-run
"""
import argparse
import sys
import subprocess
import json
from datetime import datetime

def delete_reasoning_engine(project_id, location, engine_id, dry_run=False, force=False):
    """Delete a reasoning engine by ID using REST API."""
    engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}"
    
    if dry_run:
        force_msg = " (with force)" if force else ""
        print(f"  [DRY RUN] Would delete: {engine_id}{force_msg}")
        return True
    
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
        endpoint = f"{base_url}/{engine_name}"
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
        }
        
        # Add force parameter if requested
        params = {}
        if force:
            params['force'] = 'true'
        
        response = requests.delete(endpoint, headers=headers, params=params, timeout=60)
        
        if response.status_code in [200, 204]:
        print(f"  ✓ Deleted: {engine_id}")
        return True
        else:
            # Try to parse error message for better user guidance
            error_msg = ""
            try:
                error_data = response.json()
                error_obj = error_data.get('error', {})
                error_msg = error_obj.get('message', '')
                
                # Check for child resources (sessions) error
                if 'child resources' in error_msg.lower() or 'contains child resources' in error_msg.lower():
                    if force:
                        # Force was requested but still failed - this shouldn't happen
                        print(f"  ✗ Failed to delete {engine_id} even with force=True")
                        print(f"    {error_msg[:300]}")
                        return False
                    else:
                        print(f"  ⚠ Skipped {engine_id}: Has active sessions")
                        print(f"    Note: Deployments with active sessions cannot be deleted.")
                        print(f"    Use --force to force delete (will delete child resources/sessions)")
                        print(f"    Or delete via Console:")
                        print(f"    https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={project_id}")
                        return "skipped"
                else:
                    print(f"  ✗ Failed to delete {engine_id}: HTTP {response.status_code}")
                    print(f"    {error_msg[:300]}")
            except (ValueError, KeyError):
                # Fallback if JSON parsing fails
                print(f"  ✗ Failed to delete {engine_id}: HTTP {response.status_code}")
                print(f"    {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ✗ Failed to delete {engine_id}: {e}")
        return False

def cleanup_old_deployments(project_id, location, agent_name, keep=1, dry_run=False, force=False):
    """Clean up old deployments, keeping only the latest N."""
    print(f"Cleaning up old deployments for: {agent_name}")
    print(f"Project: {project_id}, Location: {location}")
    print(f"Keeping: {keep} latest deployment(s)")
    print(f"Mode: {'DRY RUN' if dry_run else 'DELETE'}")
    if force:
        print(f"Force delete: ENABLED (will delete child resources/sessions)")
    print(f"{'='*80}")
    
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
            return
        
        data = response.json()
        engines = data.get('reasoningEngines', [])
        
        # Filter by agent name
        filtered = [e for e in engines if agent_name.lower() in e.get('displayName', '').lower()]
        
        if not filtered:
            print(f"No deployments found for: {agent_name}")
            return
        
        # Sort by createTime (newest first)
        filtered.sort(key=lambda x: x.get('createTime', ''), reverse=True)
        
        print(f"\nFound {len(filtered)} deployment(s) for {agent_name}:")
        for i, engine in enumerate(filtered, 1):
            display_name = engine.get('displayName', 'N/A')
            engine_id = engine['name'].split('/')[-1]
            create_time = engine.get('createTime', 'N/A')
            print(f"  {i}. {display_name} ({engine_id}) - {create_time}")
        
        # Determine which to delete
        to_keep = filtered[:keep]
        to_delete = filtered[keep:]
        
        if not to_delete:
            print(f"\n✓ No old deployments to clean up (only {len(to_keep)} deployment(s) exist)")
            return
        
        print(f"\nKeeping {len(to_keep)} deployment(s):")
        for engine in to_keep:
            engine_id = engine['name'].split('/')[-1]
            print(f"  - {engine_id}")
        
        print(f"\nDeleting {len(to_delete)} old deployment(s):")
        deleted_count = 0
        skipped_count = 0
        failed_count = 0
        for engine in to_delete:
            engine_id = engine['name'].split('/')[-1]
            result = delete_reasoning_engine(project_id, location, engine_id, dry_run, force)
            if result is True:
                deleted_count += 1
            elif result == "skipped":
                skipped_count += 1
            else:
                failed_count += 1
        
        print(f"\n{'='*80}")
        if dry_run:
            print(f"[DRY RUN] Would delete {deleted_count} deployment(s)")
            print("Run without --dry-run to actually delete")
        else:
            print(f"✓ Deleted {deleted_count} old deployment(s)")
            if skipped_count > 0:
                print(f"⚠ Skipped {skipped_count} deployment(s) with active sessions")
                print(f"   These deployments cannot be deleted while they have active sessions.")
                print(f"   Options:")
                print(f"   1. Run with --force to force delete (will delete child resources/sessions)")
                print(f"   2. Wait 30-60 minutes for sessions to expire and run cleanup again")
                print(f"   3. Delete manually via Console:")
                print(f"      https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={project_id}")
            if failed_count > 0:
                print(f"✗ Failed to delete {failed_count} deployment(s)")
            print(f"✓ Kept {len(to_keep)} latest deployment(s)")
        
    except ImportError:
        print("Error: 'requests' library not available")
        print("Install with: pip install requests")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Clean up old Agent Engine deployments",
        epilog="""
Note about sessions:
  Deployments with active sessions cannot be deleted until sessions expire,
  unless you use --force which will delete child resources (sessions) as well.
  
  Options:
    1. Use --force to force delete deployments with active sessions
    2. Wait 30-60 minutes for sessions to expire automatically
    3. Delete manually via Google Cloud Console
        """
    )
    parser.add_argument("--agent-name", required=True, help="Agent name to clean up (e.g., bq_agent_mick)")
    parser.add_argument("--project", help="GCP project ID", default=None)
    parser.add_argument("--location", default="us-central1", help="GCP location")
    parser.add_argument("--keep", type=int, default=1, help="Number of latest deployments to keep (default: 1)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    parser.add_argument("--force", action="store_true", help="Force delete deployments with active sessions (deletes child resources)")
    
    args = parser.parse_args()
    
    # Get project ID
    project_id = args.project
    if not project_id:
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
            sys.exit(1)
    
    if args.keep < 1:
        print("Error: --keep must be at least 1")
        sys.exit(1)
    
    cleanup_old_deployments(project_id, args.location, args.agent_name, args.keep, args.dry_run, args.force)

if __name__ == "__main__":
    main()
