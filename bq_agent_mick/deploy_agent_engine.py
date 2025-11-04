#!/usr/bin/env python3
"""
Deploy bq_agent_mick to Vertex AI Agent Engine.

According to the Vertex AI Agent Engine documentation:
https://docs.cloud.google.com/agent-builder/agent-engine/develop/adk

Agents are deployed using the ADK deployment workflow, which packages
the agent code and deploys it to Vertex AI Agent Engine.

Usage:
    python deploy_agent_engine.py [--project PROJECT_ID] [--location LOCATION] [--agent-name NAME]
"""

import argparse
import os
import sys
import subprocess
import re
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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


def check_lro_via_gcloud(operation_name, project_id, location, max_wait_minutes=15):
    """
    Check LRO status using gcloud CLI (more reliable for Agent Engine).
    
    Returns:
        True if completed successfully, False if still running/failed
    """
    try:
        # Extract operation ID from operation name
        operation_id = operation_name.split('/')[-1]
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        poll_interval = 15  # Check every 15 seconds
        
        while time.time() - start_time < max_wait_seconds:
            try:
                # Check operation status via gcloud
                result = subprocess.run(
                    [
                        "gcloud", "ai", "operations", "describe", operation_id,
                        "--region", location,
                        "--project", project_id,
                        "--format", "json"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    op_data = json.loads(result.stdout)
                    
                    if op_data.get("done", False):
                        if "error" in op_data:
                            print(f"\n✗ Deployment failed: {op_data['error'].get('message', 'Unknown error')}")
                            return False
                        else:
                            print(f"\n✓ Operation completed successfully!")
                            return True
                    else:
                        # Still running
                        elapsed = int(time.time() - start_time)
                        print(f"   Still deploying... ({elapsed}s elapsed)", end='\r')
                        time.sleep(poll_interval)
                else:
                    # Operation might not exist yet or different format
                    elapsed = int(time.time() - start_time)
                    if elapsed < 30:  # Give it 30 seconds before giving up
                        print(f"   Waiting for operation to appear... ({elapsed}s elapsed)", end='\r')
                        time.sleep(5)
                    else:
                        # Try checking agent directly in console
                        return None  # Let caller handle fallback
                        
            except subprocess.TimeoutExpired:
                # gcloud command timed out, continue polling
                time.sleep(poll_interval)
            except json.JSONDecodeError:
                # Invalid JSON response, continue polling
                time.sleep(poll_interval)
            except Exception as e:
                # Other error, continue with polling
                time.sleep(poll_interval)
        
        return None  # Timeout - let caller decide
        
    except Exception:
        return None  # Fallback to Python API


def poll_lro_status(lro_name, project_id, location, max_wait_minutes=15):
    """
    Poll the Long Running Operation (LRO) status until it completes.
    
    Args:
        lro_name: Full LRO resource name (e.g., projects/.../reasoningEngines/...)
        project_id: GCP project ID
        location: Region where the operation is running
        max_wait_minutes: Maximum time to wait in minutes
    
    Returns:
        True if LRO completed successfully, False otherwise
    """
    try:
        from google.cloud import aiplatform
        from google.cloud.aiplatform import operations
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        # Extract operation ID from LRO name
        # Format: projects/PROJECT/locations/LOCATION/reasoningEngines/ID
        # Operation: projects/PROJECT/locations/LOCATION/operations/ID
        lro_parts = lro_name.split('/')
        if len(lro_parts) >= 8 and lro_parts[-2] == 'reasoningEngines':
            operation_id = lro_parts[-1]
            operation_name = f"projects/{project_id}/locations/{location}/operations/{operation_id}"
        else:
            print(f"⚠ Could not parse LRO name: {lro_name}")
            return False
        
        print(f"\n   Monitoring operation: {operation_name}")
        
        # Try using gcloud CLI first (more reliable for Agent Engine operations)
        gcloud_result = check_lro_via_gcloud(operation_name, project_id, location, max_wait_minutes)
        if gcloud_result is True:
            return True
        elif gcloud_result is False:
            return False
        # gcloud_result is None - fallback to Python API
        
        # Fallback to Python API
        # Poll for operation status
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        poll_interval = 10  # Check every 10 seconds
        
        while time.time() - start_time < max_wait_seconds:
            try:
                # Get operation status
                operation = operations.OperationsClient().get_operation(
                    name=operation_name
                )
                
                if operation.done:
                    if operation.error:
                        print(f"\n✗ Deployment failed: {operation.error.message}")
                        return False
                    else:
                        print(f"\n✓ Operation completed successfully!")
                        return True
                else:
                    # Still running
                    elapsed = int(time.time() - start_time)
                    print(f"   Still deploying... ({elapsed}s elapsed)", end='\r')
                    time.sleep(poll_interval)
                    
            except Exception as e:
                # Operation might not be immediately available or API may differ
                print(f"\n⚠ Could not check operation status: {e}")
                print(f"   Operation may still be running. Check Console:")
                print(f"   https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={project_id}")
                return False
        
        print(f"\n⚠ Deployment timed out after {max_wait_minutes} minutes")
        print(f"   Operation may still be running. Check Console:")
        print(f"   https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={project_id}")
        return False
        
    except ImportError:
        print("\n⚠ Could not import google.cloud.aiplatform for LRO polling")
        print("   Install with: pip install google-cloud-aiplatform")
        return False
    except Exception as e:
        print(f"\n⚠ Error polling LRO status: {e}")
        return False


def check_adk_deployment_methods():
    """Check what deployment methods are available in ADK."""
    print("\nChecking ADK deployment capabilities...")
    
    try:
        # Check ADK help for deploy commands
        result = subprocess.run(
            ["adk", "--help"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check if there are deploy-related commands
        help_text = result.stdout.lower()
        
        if "deploy" in help_text or "agent" in help_text:
            print("✓ ADK deployment commands available")
            # Show relevant commands
            print("\nAvailable ADK commands:")
            subprocess.run(["adk", "--help"], check=False)
            return True
        else:
            print("⚠ ADK may not have direct deployment commands")
            print("  Check ADK documentation for deployment workflow")
            return False
            
    except Exception as e:
        print(f"✗ Error checking ADK: {e}")
        return False


def create_staging_bucket(project_id, bucket_name, location):
    """Create a GCS bucket for staging deployment artifacts if it doesn't exist.
    
    Args:
        project_id: GCP project ID
        bucket_name: Bucket name without gs:// prefix
        location: Bucket location
    """
    try:
        from google.cloud import storage
        
        # Remove gs:// prefix if present
        if bucket_name.startswith("gs://"):
            bucket_name = bucket_name.replace("gs://", "")
        
        print(f"Checking staging bucket: gs://{bucket_name}...")
        client = storage.Client(project=project_id)
        
        try:
            bucket = client.bucket(bucket_name)
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


def deploy_using_adk_cli(project_id, location, agent_name="bq_agent_mick", staging_bucket=None):
    """
    Deploy using ADK CLI command: adk deploy agent_engine
    
    Command format:
    adk deploy agent_engine --project=PROJECT --region=REGION 
    --staging_bucket=gs://BUCKET --display_name=NAME path/to/agent
    """
    print(f"\nDeploying {agent_name} to Vertex AI Agent Engine...")
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    
    # Get the agent directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    agent_dir = current_dir  # bq_agent_mick directory
    
    # Create staging bucket if not provided
    if not staging_bucket:
        staging_bucket = f"{project_id}-agent-engine-staging"
    
    # Ensure staging_bucket has gs:// prefix (required by ADK)
    if not staging_bucket.startswith("gs://"):
        staging_bucket_name = staging_bucket
        staging_bucket = f"gs://{staging_bucket}"
    else:
        # Extract bucket name for bucket creation
        staging_bucket_name = staging_bucket.replace("gs://", "")
    
    print(f"Staging bucket: {staging_bucket}")
    print(f"Agent directory: {agent_dir}")
    
    # Create bucket if needed (use bucket name without gs:// prefix)
    create_staging_bucket(project_id, staging_bucket_name, location)
    
    # Build the deployment command
    cmd = [
        "adk", "deploy", "agent_engine",
        "--project", project_id,
        "--region", location,
        "--staging_bucket", staging_bucket,
        "--display_name", agent_name,
        "--description", "BigQuery agent for billing data analysis",
        agent_dir
    ]
    
    print(f"\nRunning deployment command...")
    print(f"Command: {' '.join(cmd)}")
    print()
    print("⏳ This may take several minutes (packaging, uploading, deploying)...")
    print("   Output will stream in real-time below:\n")
    
    try:
        # Run with real-time output streaming instead of capturing
        # This prevents the appearance of hanging when ADK is processing
        process = subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        # Stream output in real-time
        output_lines = []
        for line in iter(process.stdout.readline, ''):
            if line:
                print(line, end='')  # Print immediately (no extra newline)
                output_lines.append(line)
        
        # Wait for process to complete
        process.wait()
        
        output = ''.join(output_lines)
        
        # Check for failure in output
        if process.returncode != 0:
            print(f"\n✗ Deployment failed with exit code {process.returncode}")
            return False
        
        if "Deploy failed" in output or ("failed" in output.lower() and "Deploy failed" in output):
            print(f"\n✗ Deployment failed:")
            return False
        
        # Extract LRO (Long Running Operation) ID from output if present
        # Pattern: "Create AgentEngine backing LRO: projects/.../locations/.../reasoningEngines/..."
        lro_pattern = r'Create AgentEngine backing LRO:\s*(projects/[^/\s]+/locations/[^/\s]+/reasoningEngines/\d+)'
        lro_match = re.search(lro_pattern, output)
        
        if lro_match:
            lro_name = lro_match.group(1)
            print(f"\n⏳ Deployment started (LRO: {lro_name})")
            print("   Waiting for deployment to complete (this may take several minutes)...")
            
            # Poll LRO status
            if poll_lro_status(lro_name, project_id, location):
                print("\n✓ Deployment completed successfully!")
                return True
            else:
                print("\n⚠ Deployment LRO is still running or failed.")
                print(f"   Check status manually or view logs:")
                print(f"   https://console.cloud.google.com/logs/query?project={project_id}")
                return False
        else:
            # No LRO found - assume immediate completion (older ADK versions)
            print("\n✓ Deployment completed successfully!")
            return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Deployment failed with exit code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠ Deployment interrupted by user")
        if 'process' in locals():
            process.terminate()
        return False
    except Exception as e:
        print(f"\n✗ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def deploy_using_python_api(project_id, location, agent_name="bq_agent_mick"):
    """
    Deploy using Python API if available.
    
    Check if google.adk has deployment capabilities.
    """
    print(f"\nChecking for Python-based deployment API...")
    
    try:
        # Add project root to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # Try to import ADK deployment modules
        try:
            from google.adk import deploy
            print("✓ Found google.adk.deploy module")
            return True
        except ImportError:
            pass
        
        try:
            from google.adk.platform import vertex
            print("✓ Found google.adk.platform.vertex module")
            return True
        except ImportError:
            pass
        
        # Check what's available in google.adk
        import google.adk
        adk_modules = [x for x in dir(google.adk) if not x.startswith('_')]
        print(f"Available ADK modules: {adk_modules}")
        
        # Look for deployment-related modules
        deploy_modules = [m for m in adk_modules if 'deploy' in m.lower() or 'platform' in m.lower()]
        if deploy_modules:
            print(f"Potential deployment modules: {deploy_modules}")
            return True
        
        print("⚠ No deployment API found in google.adk")
        return False
        
    except Exception as e:
        print(f"✗ Error checking Python API: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_manual_deployment_instructions(project_id, location, agent_name):
    """Print manual deployment instructions based on the documentation."""
    print("\n" + "=" * 60)
    print("Manual Deployment Instructions")
    print("=" * 60)
    
    print("\nAccording to Vertex AI Agent Engine documentation:")
    print("https://docs.cloud.google.com/agent-builder/agent-engine/deploy/adk")
    
    print("\n1. Ensure your agent is properly structured:")
    print(f"   - Agent module: bq_agent_mick.agent")
    print(f"   - Agent variable: root_agent")
    
    print("\n2. Follow the ADK deployment workflow:")
    print("   - Package your agent code")
    print("   - Deploy using ADK CLI or Python API")
    
    print("\n3. Alternative: Use the Console workflow:")
    print("   a. Go to: https://console.cloud.google.com/vertex-ai/agents/agent-engines")
    print("   b. Click 'Develop agent'")
    print("   c. Select 'Agent Development Kit' as your framework")
    print("   d. Follow the deployment guide")
    
    print("\n4. Or use the deployment guide link in the Console")
    print("   (The 'Deployment guide' button in the Agent Engine page)")
    
    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    print("\n1. Review the official deployment documentation:")
    print("   https://docs.cloud.google.com/agent-builder/agent-engine/deploy/adk")
    
    print("\n2. Check the ADK deployment guide:")
    print("   The Console shows a 'Deployment guide' button - use that")
    
    print("\n3. Use the 'Develop agent' workflow:")
    print("   This guides you through the proper deployment process")
    
    print(f"\n4. Your agent configuration:")
    print(f"   - Project: {project_id}")
    print(f"   - Location: {location}")
    print(f"   - Agent: {agent_name}")
    print(f"   - Module: bq_agent_mick.agent")


def main():
    parser = argparse.ArgumentParser(
        description="Deploy bq_agent_mick to Vertex AI Agent Engine"
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
        "--agent-name",
        default="bq_agent_mick",
        help="Agent display name (default: bq_agent_mick)"
    )
    parser.add_argument(
        "--staging-bucket",
        default=None,
        help="GCS bucket for staging deployment artifacts (default: PROJECT_ID-agent-engine-staging)"
    )
    
    args = parser.parse_args()
    
    # Validate project ID
    if not args.project or args.project == "YOUR_PROJECT_ID":
        print("Error: Project ID required.")
        print("Set GCP_PROJECT_ID, GOOGLE_CLOUD_PROJECT, or BQ_PROJECT environment variable")
        print("Or use --project argument")
        sys.exit(1)
    
    print("=" * 60)
    print("Deploying bq_agent_mick to Vertex AI Agent Engine")
    print("=" * 60)
    print(f"Project: {args.project}")
    print(f"Location: {args.location}")
    print(f"Agent Name: {args.agent_name}")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n✗ Prerequisites check failed. Please install missing tools.")
        sys.exit(1)
    
    # Check ADK deployment methods
    has_deploy_commands = check_adk_deployment_methods()
    
    # Try Python API
    has_python_api = deploy_using_python_api(args.project, args.location, args.agent_name)
    
    # Deploy using ADK CLI (this is the correct method!)
    if has_deploy_commands:
        success = deploy_using_adk_cli(
            args.project, 
            args.location, 
            args.agent_name,
            args.staging_bucket
        )
        if success:
            print("\n" + "=" * 60)
            print("✓ Deployment completed successfully!")
            print("=" * 60)
            print(f"\nYour agent is now deployed to Vertex AI Agent Engine.")
            print(f"View it in the Console:")
            print(f"https://console.cloud.google.com/vertex-ai/agents/agent-engines?project={args.project}")
            sys.exit(0)
        else:
            print("\n✗ Deployment failed. Check errors above.")
            sys.exit(1)
    
    # If automated deployment doesn't work, provide manual instructions
    print_manual_deployment_instructions(args.project, args.location, args.agent_name)
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("\nAutomated deployment may not be available in your ADK version.")
    print("Please follow the manual deployment instructions above.")
    print("\nFor the most up-to-date deployment instructions, visit:")
    print("https://docs.cloud.google.com/agent-builder/agent-engine/deploy/adk")


if __name__ == "__main__":
    main()
