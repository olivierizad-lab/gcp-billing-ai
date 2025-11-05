#!/usr/bin/env python3
"""
Shared deployment script for deploying agents to Vertex AI Agent Engine.

This script can be used to deploy any agent directory that has:
- An agent_engine_app.py file that exports an 'adk_app' instance
- Or an agent.py file that exports a 'root_agent' instance

According to the Vertex AI Agent Engine documentation:
https://docs.cloud.google.com/agent-builder/agent-engine/develop/adk

Usage:
    python scripts/deploy_agent_engine.py --agent-dir bq_agent_mick [options]
    python scripts/deploy_agent_engine.py --agent-dir bq_agent [options]
"""

import argparse
import os
import sys
import subprocess
import re
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import cleanup functionality
from scripts.cleanup_old_deployments import cleanup_old_deployments


def check_prerequisites():
    """Check if required tools are available."""
    print("Checking prerequisites...")
    
    # Check ADK CLI
    try:
        result = subprocess.run(
            ["adk", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ ADK CLI found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ ADK CLI not found.")
        print("  Install with: pip install google-adk")
        return False
    
    # Check gcloud
    try:
        subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ gcloud CLI found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ gcloud CLI not found.")
        print("  Install Google Cloud SDK: https://cloud.google.com/sdk")
        return False
    
    return True


def check_agent_directory(agent_dir):
    """Check if agent directory is valid and has required files."""
    agent_path = project_root / agent_dir
    
    if not agent_path.exists():
        print(f"✗ Agent directory not found: {agent_dir}")
        return False
    
    if not agent_path.is_dir():
        print(f"✗ Path is not a directory: {agent_dir}")
        return False
    
    # Check for agent_engine_app.py or agent.py
    has_app = (agent_path / "agent_engine_app.py").exists()
    has_agent = (agent_path / "agent.py").exists()
    
    if not has_app and not has_agent:
        print(f"✗ Agent directory missing required files:")
        print(f"  Expected: {agent_dir}/agent_engine_app.py OR {agent_dir}/agent.py")
        return False
    
    print(f"✓ Agent directory found: {agent_dir}")
    if has_app:
        print(f"  Found: agent_engine_app.py")
    if has_agent:
        print(f"  Found: agent.py")
    
    return True


def create_staging_bucket(project_id, bucket_name, location):
    """Create GCS staging bucket if it doesn't exist."""
    try:
        from google.cloud import storage
        
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        
        try:
            if bucket.exists():
                print(f"✓ Staging bucket already exists: gs://{bucket_name}")
                return True
        except Exception:
            pass
        
        # Create bucket if it doesn't exist
        print(f"Creating staging bucket: gs://{bucket_name}...")
        bucket = client.create_bucket(bucket_name, location=location)
        print(f"✓ Staging bucket created: gs://{bucket_name}")
        return True
        
    except Exception as e:
        print(f"⚠ Could not create staging bucket: {e}")
        print(f"Please create manually: gsutil mb -p {project_id} -l {location} gs://{bucket_name}")
        return False


def deploy_agent(project_id, location, agent_dir, agent_name, staging_bucket=None, 
                 cleanup_before=False, cleanup_after=True, keep_deployments=1):
    """
    Deploy agent using ADK CLI command: adk deploy agent_engine
    
    Args:
        project_id: GCP project ID
        location: GCP location/region
        agent_dir: Agent directory name
        agent_name: Agent display name
        staging_bucket: GCS staging bucket (optional)
        cleanup_before: If True, clean up old deployments before deploying
        cleanup_after: If True, clean up old deployments after successful deployment
        keep_deployments: Number of latest deployments to keep (default: 1)
    """
    print(f"\nDeploying {agent_name} to Vertex AI Agent Engine...")
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    
    agent_path = project_root / agent_dir
    
    # Create staging bucket if not provided
    if not staging_bucket:
        staging_bucket = f"{project_id}-agent-engine-staging"
    
    # Ensure staging_bucket has gs:// prefix (required by ADK)
    if not staging_bucket.startswith("gs://"):
        staging_bucket_name = staging_bucket
        staging_bucket = f"gs://{staging_bucket}"
    else:
        staging_bucket_name = staging_bucket.replace("gs://", "")
    
    print(f"Staging bucket: {staging_bucket}")
    print(f"Agent directory: {agent_path}")
    
    # Create bucket if needed
    create_staging_bucket(project_id, staging_bucket_name, location)
    
    # Clean up old deployments before deploying (if requested)
    if cleanup_before:
        print(f"\n{'='*60}")
        print("Cleaning up old deployments before deployment...")
        print(f"{'='*60}")
        try:
            cleanup_old_deployments(project_id, location, agent_name, keep=keep_deployments, dry_run=False)
            print("✓ Pre-deployment cleanup completed")
        except Exception as e:
            print(f"⚠ Pre-deployment cleanup failed (continuing with deployment): {e}")
    
    # Build the deployment command
    cmd = [
        "adk", "deploy", "agent_engine",
        "--project", project_id,
        "--region", location,
        "--staging_bucket", staging_bucket,
        "--display_name", agent_name,
        "--description", f"BigQuery agent for billing data analysis ({agent_name})",
        str(agent_path)
    ]
    
    print(f"\nRunning deployment command...")
    print(f"Command: {' '.join(cmd)}")
    print(f"\n⏳ This may take several minutes (packaging, uploading, deploying)...")
    print(f"   Output will stream in real-time below:\n")
    print("=" * 60)
    
    try:
        # Run the deployment command
        result = subprocess.run(
            cmd,
            check=False,  # Don't raise on error, we'll check the result
            text=True
        )
        
        print("=" * 60)
        
        if result.returncode == 0:
            print(f"\n✓ Deployment completed successfully!")
            
            # Clean up old deployments after successful deployment (default behavior)
            if cleanup_after:
                print(f"\n{'='*60}")
                print("Cleaning up old deployments (keeping latest)...")
                print(f"{'='*60}")
                try:
                    cleanup_old_deployments(project_id, location, agent_name, keep=keep_deployments, dry_run=False)
                    print("✓ Post-deployment cleanup completed")
                except Exception as e:
                    print(f"⚠ Post-deployment cleanup failed (deployment still successful): {e}")
            
            print(f"\nNext steps:")
            print(f"1. Check the console: https://console.cloud.google.com/vertex-ai/agents/agent-engines")
            print(f"2. Get latest deployment ID: make list-deployments AGENT_NAME={agent_name}")
            print(f"3. Update REASONING_ENGINE_ID in your .env file or query script")
            print(f"4. Test the agent with: python -m {agent_dir}.query_agent 'Your question'")
            return True
        else:
            print(f"\n✗ Deployment failed (exit code: {result.returncode})")
            print(f"\nCheck the error messages above for details.")
            return False
            
    except FileNotFoundError:
        print(f"\n✗ Error: 'adk' command not found")
        print(f"  Install with: pip install google-adk")
        return False
    except Exception as e:
        print(f"\n✗ Deployment error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Deploy an ADK agent to Vertex AI Agent Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/deploy_agent_engine.py --agent-dir bq_agent_mick
  python scripts/deploy_agent_engine.py --agent-dir bq_agent --project my-project
  python scripts/deploy_agent_engine.py --agent-dir bq_agent_mick --location us-west1
        """
    )
    
    parser.add_argument(
        "--agent-dir",
        required=True,
        help="Agent directory name (e.g., 'bq_agent_mick', 'bq_agent')"
    )
    parser.add_argument(
        "--project",
        default=None,
        help="GCP project ID (default: from gcloud config or environment)"
    )
    parser.add_argument(
        "--location",
        default="us-central1",
        help="GCP location/region (default: us-central1)"
    )
    parser.add_argument(
        "--agent-name",
        default=None,
        help="Agent display name (default: same as agent-dir)"
    )
    parser.add_argument(
        "--staging-bucket",
        default=None,
        help="GCS staging bucket (default: {PROJECT_ID}-agent-engine-staging)"
    )
    parser.add_argument(
        "--cleanup-before",
        action="store_true",
        help="Clean up old deployments before deploying (default: False)"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup of old deployments after deployment (default: cleanup after)"
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=1,
        help="Number of latest deployments to keep when cleaning up (default: 1, like Cloud Run)"
    )
    
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
            pass
    
    if not project_id:
        print("✗ Error: PROJECT_ID must be set")
        print("  Set it with: --project PROJECT_ID")
        print("  Or set gcloud default: gcloud config set project PROJECT_ID")
        sys.exit(1)
    
    # Determine agent name
    agent_name = args.agent_name or args.agent_dir
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Check agent directory
    if not check_agent_directory(args.agent_dir):
        sys.exit(1)
    
    # Deploy with cleanup options
    success = deploy_agent(
        project_id=project_id,
        location=args.location,
        agent_dir=args.agent_dir,
        agent_name=agent_name,
        staging_bucket=args.staging_bucket,
        cleanup_before=args.cleanup_before,
        cleanup_after=not args.no_cleanup,  # Default to True unless --no-cleanup is set
        keep_deployments=args.keep
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
