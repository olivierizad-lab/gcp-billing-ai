#!/usr/bin/env python3
"""
Deployment script for bq_agent_mick to Vertex AI Agent Builder.

Usage:
    python deploy.py [--project PROJECT_ID] [--location LOCATION] [--agent-name NAME]
"""

import argparse
import os
import sys
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv()


def check_prerequisites():
    """Check if required tools and configurations are available."""
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
        print("✗ ADK CLI not found. Please install google-adk package.")
        return False
    
    # Check gcloud
    try:
        result = subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ gcloud CLI found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ gcloud CLI not found. Please install Google Cloud SDK.")
        return False
    
    # Check environment variables
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("✗ GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT not set")
        return False
    print(f"✓ Project ID: {project_id}")
    
    return True


def enable_apis(project_id):
    """Enable required Google Cloud APIs."""
    print(f"\nEnabling required APIs for project {project_id}...")
    
    apis = [
        "aiplatform.googleapis.com",
        "bigquery.googleapis.com",
    ]
    
    for api in apis:
        try:
            subprocess.run(
                ["gcloud", "services", "enable", api, "--project", project_id],
                check=True,
                capture_output=True
            )
            print(f"✓ Enabled {api}")
        except subprocess.CalledProcessError as e:
            print(f"⚠ Warning: Could not enable {api}: {e}")
            # Continue anyway as API might already be enabled


def deploy_agent_python(project_id, location, agent_name="bq_agent_mick"):
    """Deploy the agent using Python API (recommended method)."""
    print(f"\nDeploying agent '{agent_name}' using Python API...")
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    
    try:
        # Import required modules
        from google.adk.vertex import VertexAgentRegistry
        from bq_agent_mick.agent import root_agent
        
        # Register the agent
        registry = VertexAgentRegistry(
            project_id=project_id,
            location=location
        )
        
        agent_resource = registry.register_agent(
            agent=root_agent,
            display_name=agent_name
        )
        
        print("✓ Agent deployed successfully!")
        print(f"Agent Resource: {agent_resource}")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Note: Make sure you're in the project root directory")
        return False
    except Exception as e:
        print(f"✗ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def deploy_agent(project_id, location, agent_name="bq_agent_mick"):
    """Deploy the agent to Vertex AI Agent Builder."""
    print(f"\nDeploying agent '{agent_name}' to Vertex AI...")
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    
    # Try Python-based deployment first (recommended)
    if deploy_agent_python(project_id, location, agent_name):
        return True
    
    print("\n⚠ Python deployment failed, trying alternative methods...")
    
    # Alternative: Try using ADK CLI (if available)
    try:
        # Check available ADK commands
        result = subprocess.run(
            ["adk", "--help"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Look for deploy or register commands in help
        if "deploy" in result.stdout.lower() or "register" in result.stdout.lower():
            print("ADK CLI deployment commands may be available")
            print("Please check ADK documentation for correct command syntax")
            print("\nExample (may vary by ADK version):")
            print(f"  adk deploy --module bq_agent_mick.agent --name {agent_name}")
        
    except Exception:
        pass
    
    return False


def verify_deployment(project_id, location, agent_name):
    """Verify the agent was deployed successfully."""
    print(f"\nVerifying deployment...")
    
    try:
        # List agents using gcloud
        cmd = [
            "gcloud", "ai", "agents", "list",
            "--project", project_id,
            "--location", location,
            "--format", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse and check if our agent is there
        import json
        agents = json.loads(result.stdout)
        
        agent_found = any(
            agent.get("displayName") == agent_name or 
            agent.get("name", "").endswith(agent_name)
            for agent in agents
        )
        
        if agent_found:
            print(f"✓ Agent '{agent_name}' found in Vertex AI")
        else:
            print(f"⚠ Agent '{agent_name}' not found in list (may take a few moments to appear)")
        
        return agent_found
        
    except Exception as e:
        print(f"⚠ Could not verify deployment: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Deploy bq_agent_mick to Vertex AI Agent Builder"
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT"),
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
        help="Agent name (default: bq_agent_mick)"
    )
    parser.add_argument(
        "--skip-api-enable",
        action="store_true",
        help="Skip enabling APIs (assumes already enabled)"
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip deployment verification"
    )
    
    args = parser.parse_args()
    
    # If project is still "YOUR_PROJECT_ID" (literal string), try environment
    if args.project == "YOUR_PROJECT_ID" or not args.project:
        env_project = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        if env_project:
            args.project = env_project
            print(f"Using project ID from environment: {args.project}")
        else:
            print("Error: Project ID required. Set GCP_PROJECT_ID environment variable or use --project")
            sys.exit(1)
    
    print("=" * 60)
    print("Deploying bq_agent_mick to Vertex AI Agent Builder")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n✗ Prerequisites check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Enable APIs
    if not args.skip_api_enable:
        enable_apis(args.project)
    
    # Deploy agent
    if not deploy_agent(args.project, args.location, args.agent_name):
        print("\n✗ Deployment failed.")
        sys.exit(1)
    
    # Verify deployment
    if not args.skip_verify:
        verify_deployment(args.project, args.location, args.agent_name)
    
    print("\n" + "=" * 60)
    print("Deployment process completed!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"1. Visit the Vertex AI Console: https://console.cloud.google.com/vertex-ai/agents")
    print(f"2. Find your agent: {args.agent_name}")
    print(f"3. Test the agent through the console or API")
    print(f"\nExample Python usage:")
    print(f"""
from google.adk.runners import Runner
from google.adk.vertex import VertexSessionService

session_service = VertexSessionService(
    project_id="{args.project}",
    location="{args.location}"
)

runner = Runner(
    agent_name="{args.agent_name}",
    app_name="billing_analysis_app",
    session_service=session_service,
)
""")


if __name__ == "__main__":
    main()
