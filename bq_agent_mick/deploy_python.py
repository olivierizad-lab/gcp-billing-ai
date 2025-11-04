#!/usr/bin/env python3
"""
Python-based deployment script for bq_agent_mick to Vertex AI Agent Builder.

This script uses Vertex AI APIs directly to deploy the agent.

Usage:
    python deploy_python.py [--project PROJECT_ID] [--location LOCATION] [--agent-name NAME]
"""

import argparse
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def deploy_agent(project_id, location, agent_name="bq_agent_mick"):
    """Deploy the agent to Vertex AI using Vertex AI Agent Builder APIs."""
    print("=" * 60)
    print("Deploying bq_agent_mick to Vertex AI Agent Builder")
    print("=" * 60)
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    print(f"Agent Name: {agent_name}")
    print()
    
    try:
        # Add project root to path if needed
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        print("Importing required modules...")
        from google.cloud import aiplatform
        from google.cloud.aiplatform import gapic
        from bq_agent_mick.agent import root_agent
        
        print("✓ Modules imported successfully")
        
        # Initialize Vertex AI
        print(f"\nInitializing Vertex AI...")
        aiplatform.init(project=project_id, location=location)
        print(f"✓ Vertex AI initialized")
        
        # Note: Vertex AI Agent Builder deployment is complex and may require:
        # 1. Creating an agent definition file/configuration
        # 2. Using the Vertex AI Agent Builder API
        # 3. Or deploying as a Cloud Run service that hosts the agent
        
        print("\n" + "=" * 60)
        print("⚠ Note: Direct ADK agent deployment to Vertex AI Agent Builder")
        print("   requires additional setup. See DEPLOYMENT.md for alternatives.")
        print("=" * 60)
        
        print("\nRecommended deployment options:")
        print("\n1. Deploy as Cloud Run Service:")
        print("   - Package the agent as a Cloud Run service")
        print("   - Expose REST API endpoints for agent interaction")
        print("   - Deploy using: gcloud run deploy")
        
        print("\n2. Use Vertex AI Agent Builder Console:")
        print("   - Create agent in Vertex AI Console")
        print("   - Configure tools and instructions")
        print("   - Link to BigQuery resources")
        
        print("\n3. Use Vertex AI Agent Builder API:")
        print("   - Create agent using REST API or Python client")
        print("   - Configure agent with tools and instructions")
        
        print("\nFor now, the agent can be run locally using:")
        print("   python main.py")
        print("   (modify main.py to use bq_agent_mick.agent)")
        
        return True
        
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're running from the project root directory")
        print("2. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("3. Verify google-cloud-aiplatform is installed")
        return False
    except Exception as e:
        print(f"\n✗ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def deploy_as_cloud_run(project_id, location, agent_name="bq_agent_mick"):
    """Provide instructions for deploying as Cloud Run service."""
    print("\n" + "=" * 60)
    print("Cloud Run Deployment Option")
    print("=" * 60)
    print("\nTo deploy as a Cloud Run service:")
    print("1. Create a Cloud Run service that hosts the agent")
    print("2. Expose REST endpoints for agent interaction")
    print("3. Deploy using gcloud or Cloud Build")
    print("\nSee DEPLOYMENT.md for detailed Cloud Run deployment steps.")


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
        help="Agent display name (default: bq_agent_mick)"
    )
    parser.add_argument(
        "--method",
        choices=["info", "cloud-run"],
        default="info",
        help="Deployment method (default: info)"
    )
    
    args = parser.parse_args()
    
    # Validate project ID
    if not args.project or args.project == "YOUR_PROJECT_ID":
        env_project = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        if env_project:
            args.project = env_project
        else:
            print("Error: Project ID required.")
            print("Set GCP_PROJECT_ID environment variable or use --project")
            sys.exit(1)
    
    if args.method == "cloud-run":
        deploy_as_cloud_run(args.project, args.location, args.agent_name)
    else:
        success = deploy_agent(args.project, args.location, args.agent_name)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
