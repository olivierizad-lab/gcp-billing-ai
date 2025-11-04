#!/usr/bin/env python3
"""
Deploy bq_agent_mick to Vertex AI Agent Builder.

Since Vertex AI Agent Builder REST API endpoints are not publicly available,
this script provides two approaches:
1. Generate configuration file for manual Console import
2. Provide instructions for Cloud Run deployment (recommended)

Usage:
    python deploy_vertex_api.py [--project PROJECT_ID] [--location LOCATION] [--agent-name NAME] [--output-config]
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_agent_config():
    """Extract agent configuration from bq_agent_mick.agent."""
    # Add project root to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        from bq_agent_mick.agent import (
            PROJECT_ID,
            DATASET,
            LOCATION,
            _build_root_agent
        )
        
        # Build agent to get full config
        import nest_asyncio
        nest_asyncio.apply()
        agent = asyncio.run(_build_root_agent())
        
        return {
            "name": agent.name,
            "model": agent.model,
            "description": agent.description,
            "instruction": agent.instruction,
            "project_id": PROJECT_ID,
            "dataset": DATASET,
            "location": LOCATION,
        }
    except Exception as e:
        print(f"Error extracting agent config: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_agent_instructions(config: Dict[str, Any]) -> str:
    """Format agent instructions with configuration details."""
    instruction = f"""You are a data science agent with access to BigQuery tools.

{config['instruction']}

Key configuration:
- Project: {config['project_id']}
- Dataset: {config['dataset']}
- Location: {config['location']}

Your capabilities:
- Inspect BigQuery table schemas and metadata
- Execute SQL SELECT queries (read-only)
- Analyze billing and cost data
- Answer questions about GCP billing patterns

Important guidelines:
- Always retrieve table schema before executing queries
- Use efficient queries and respect data limits
- Present results in clear, readable formats
- Explain your query approach when helpful
"""
    return instruction


def generate_agent_config_file(config: Dict[str, Any], output_path: str) -> bool:
    """Generate a configuration file that can be used for manual agent creation."""
    config['instruction'] = create_agent_instructions(config)
    
    agent_config = {
        "agent": {
            "displayName": config["name"],
            "description": config["description"],
            "defaultLanguageCode": "en",
            "instructions": config["instruction"],
            "model": config["model"],
            "configuration": {
                "projectId": config["project_id"],
                "location": config["location"],
                "bigQuery": {
                    "projectId": config["project_id"],
                    "datasetId": config["dataset"].split(".")[-1] if "." in config["dataset"] else config["dataset"],
                    "location": config["location"],
                }
            }
        },
        "tools": [
            {
                "type": "BIG_QUERY",
                "name": "BigQuery Toolset",
                "description": "Tools for querying BigQuery data",
                "configuration": {
                    "projectId": config["project_id"],
                    "datasetId": config["dataset"],
                    "location": config["location"],
                    "readOnly": True
                }
            }
        ]
    }
    
    try:
        with open(output_path, 'w') as f:
            json.dump(agent_config, f, indent=2)
        print(f"✓ Configuration file generated: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to generate config file: {e}")
        return False


def print_cloud_run_instructions(config: Dict[str, Any], project_id: str, location: str):
    """Print instructions for Cloud Run deployment (recommended approach)."""
    print("\n" + "=" * 60)
    print("RECOMMENDED: Deploy as Cloud Run Service")
    print("=" * 60)
    print("\nSince Vertex AI Agent Builder API is not publicly available,")
    print("the recommended approach for ADK agents is Cloud Run deployment.\n")
    
    print("Step 1: Create a FastAPI service wrapper")
    print("-" * 60)
    service_code = f'''from fastapi import FastAPI
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from bq_agent_mick.agent import root_agent
from pydantic import BaseModel

app = FastAPI()
session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name="bq_agent_mick_service",
    session_service=session_service,
)

class QueryRequest(BaseModel):
    query: str
    user_id: str = "default_user"
    session_id: str = "default_session"

@app.post("/query")
async def query_agent(request: QueryRequest):
    from google.genai import types
    
    content = types.Content(
        role="user",
        parts=[types.Part(text=request.query)]
    )
    
    session = await session_service.create_session(
        app_name="bq_agent_mick_service",
        user_id=request.user_id,
        session_id=request.session_id
    )
    
    response_text = ""
    async for event in runner.run_async(
        user_id=request.user_id,
        session_id=request.session_id,
        new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
            break
    
    return {{"response": response_text}}

@app.get("/health")
async def health():
    return {{"status": "healthy"}}
'''
    print(service_code)
    print("\nSave this to: bq_agent_mick/service.py")
    
    print("\nStep 2: Create Dockerfile")
    print("-" * 60)
    dockerfile = '''FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "bq_agent_mick.service:app", "--host", "0.0.0.0", "--port", "8080"]
'''
    print(dockerfile)
    
    print("\nStep 3: Deploy to Cloud Run")
    print("-" * 60)
    deploy_cmd = f'''gcloud run deploy bq-agent-mick \\
  --source . \\
  --platform managed \\
  --region {location} \\
  --allow-unauthenticated \\
  --set-env-vars BQ_PROJECT={config['project_id']},BQ_DATASET={config['dataset']},BQ_LOCATION={config['location']} \\
  --project {project_id}'''
    print(deploy_cmd)
    
    print("\nStep 4: Test the deployment")
    print("-" * 60)
    print(f"After deployment, get the service URL and test:")
    print(f'''curl -X POST "https://YOUR-SERVICE-URL/query" \\
  -H "Content-Type: application/json" \\
  -d '{{"query": "What is the total cost for invoice month 202510?"}}' ''')


def print_console_instructions(config: Dict[str, Any]):
    """Print instructions for manual Console setup."""
    config['instruction'] = create_agent_instructions(config)
    
    print("\n" + "=" * 60)
    print("Alternative: Create Agent in Vertex AI Console")
    print("=" * 60)
    print("\n1. Go to: https://console.cloud.google.com/vertex-ai/agents")
    print("2. Click 'Create Agent'")
    print("3. Configure with the following settings:\n")
    
    print("   Display Name:", config["name"])
    print("   Description:", config["description"])
    print("   Model:", config["model"])
    print("   Language Code: en")
    print("\n   Instructions:")
    print("   " + "-" * 56)
    for line in config["instruction"].split("\n"):
        print(f"   {line}")
    print("   " + "-" * 56)
    
    print("\n4. Add BigQuery Tool:")
    print(f"   - Project ID: {config['project_id']}")
    print(f"   - Dataset: {config['dataset']}")
    print(f"   - Location: {config['location']}")
    print("   - Enable read-only mode")
    
    print("\n5. Save and deploy")


def deploy_agent(
    project_id: str,
    location: str,
    agent_name: str = "bq_agent_mick",
    output_config: bool = False
) -> bool:
    """Main deployment function - provides deployment options."""
    
    print("=" * 60)
    print("Deploying bq_agent_mick to Vertex AI")
    print("=" * 60)
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    print(f"Agent Name: {agent_name}")
    print()
    
    # Extract agent configuration
    print("Extracting agent configuration...")
    config = get_agent_config()
    if not config:
        print("✗ Failed to extract agent configuration")
        return False
    
    print("✓ Configuration extracted:")
    print(f"  Name: {config['name']}")
    print(f"  Model: {config['model']}")
    print(f"  Description: {config['description']}")
    print(f"  Project: {config['project_id']}")
    print(f"  Dataset: {config['dataset']}")
    
    # Generate config file if requested
    if output_config:
        config_file = f"{agent_name}_config.json"
        generate_agent_config_file(config, config_file)
        print(f"\n✓ Use this config file when creating the agent in Console")
    
    # Print deployment options
    print_cloud_run_instructions(config, project_id, location)
    print_console_instructions(config)
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("\n✓ Agent configuration extracted successfully")
    print("✓ Deployment instructions provided above")
    print("\nRecommended: Use Cloud Run deployment for ADK agents")
    print("Alternative: Create agent manually in Vertex AI Console")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Deploy bq_agent_mick - Generate configuration and deployment instructions"
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
        "--output-config",
        action="store_true",
        help="Generate a JSON configuration file for manual import"
    )
    
    args = parser.parse_args()
    
    # Validate project ID
    if not args.project or args.project == "YOUR_PROJECT_ID":
        print("Error: Project ID required.")
        print("Set GCP_PROJECT_ID, GOOGLE_CLOUD_PROJECT, or BQ_PROJECT environment variable")
        print("Or use --project argument")
        sys.exit(1)
    
    # Deploy agent (provides instructions)
    success = deploy_agent(
        project_id=args.project,
        location=args.location,
        agent_name=args.agent_name,
        output_config=args.output_config
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
