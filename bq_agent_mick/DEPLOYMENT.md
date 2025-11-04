# Deploying bq_agent_mick to Vertex AI Agent Builder

## Overview

This guide explains how to deploy the `bq_agent_mick` agent for production use. Google ADK agents can be deployed in several ways:

1. **Cloud Run Service** - Package the agent as a web service
2. **Vertex AI Agent Builder** - Create an agent configuration in Vertex AI
3. **Local/Localhost** - Run directly for development/testing

## Important Note

The Google ADK (`google-adk`) package is primarily designed for local agent development and execution. There isn't a direct "deploy to Vertex AI" command in ADK. Instead, you have several deployment options outlined below.

## Prerequisites

1. **Google Cloud Project** with required APIs enabled
2. **Authentication** set up with appropriate permissions
3. **Environment Variables** configured
4. **Python dependencies** installed

## Step 1: Enable Required APIs

Enable the necessary Google Cloud APIs:

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable run.googleapis.com  # If using Cloud Run
```

## Step 2: Set Environment Variables

Configure the required environment variables:

```bash
export GCP_PROJECT_ID="your-project-id"
export BQ_PROJECT="your-project-id"
export BQ_DATASET="project.dataset"
export BQ_LOCATION="US"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

Or create a `.env` file:

```bash
GCP_PROJECT_ID=your-project-id
BQ_PROJECT=your-project-id
BQ_DATASET=your-project.dataset
BQ_LOCATION=US
```

## Step 3: Authenticate

Set up Application Default Credentials:

```bash
gcloud auth application-default login
```

Or use a service account:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Deployment Options

### Option A: Deploy as Cloud Run Service (Recommended for ADK Agents)

This is the recommended approach for ADK agents - package them as a Cloud Run service.

#### Step 1: Create a Flask/FastAPI service wrapper

Create `bq_agent_mick/service.py`:

```python
from fastapi import FastAPI, HTTPException
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
    
    return {"response": response_text}
```

#### Step 2: Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fastapi uvicorn

COPY . .

CMD ["uvicorn", "bq_agent_mick.service:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### Step 3: Deploy to Cloud Run

```bash
gcloud run deploy bq-agent-mick \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars BQ_PROJECT=$BQ_PROJECT,BQ_DATASET=$BQ_DATASET
```

### Option B: Use Vertex AI Agent Builder Console

1. Go to [Vertex AI Agent Builder Console](https://console.cloud.google.com/vertex-ai/agents)
2. Click "Create Agent"
3. Configure the agent with:
   - Name: `bq_agent_mick`
   - Instructions: Same as in `bq_agent_mick/agent.py`
   - Tools: BigQuery toolset
   - Model: `gemini-2.5-flash`
4. Link BigQuery datasets/tables
5. Deploy

### Option C: Vertex AI Agent Builder API (Automated)

Use the provided deployment script to create agents programmatically using the Vertex AI Agent Builder REST API.

#### Using the Deployment Script

The `deploy_vertex_api.py` script automatically:
1. Extracts agent configuration from `bq_agent_mick.agent`
2. Creates an agent using Vertex AI Agent Builder REST API
3. Configures the agent with model, instructions, and BigQuery tools

**Basic usage:**
```bash
python bq_agent_mick/deploy_vertex_api.py \
  --project YOUR_PROJECT_ID \
  --location us-central1 \
  --agent-name bq_agent_mick
```

**With environment variables:**
```bash
export GCP_PROJECT_ID="your-project-id"
export BQ_PROJECT="your-project-id"
python bq_agent_mick/deploy_vertex_api.py
```

**Advanced options:**
```bash
python bq_agent_mick/deploy_vertex_api.py \
  --project YOUR_PROJECT_ID \
  --location us-central1 \
  --agent-name bq_agent_mick \
  --method rest  # Options: 'rest' (REST API) or 'python' (experimental)
```

#### What the Script Does

1. **Configuration Extraction**: Reads agent configuration from `bq_agent_mick/agent.py`:
   - Agent name, model, description, instructions
   - BigQuery project, dataset, and location
   - Tool configurations

2. **API Deployment**: Attempts multiple API endpoint structures:
   - Tries different Vertex AI API endpoints
   - Tests various payload formats (camelCase, snake_case)
   - Handles different API versions automatically

3. **Tool Configuration**: Automatically configures:
   - BigQuery tool with project/dataset/location
   - Agent instructions with context
   - Model specification (gemini-2.5-flash)

#### Prerequisites for API Deployment

1. **APIs Enabled**:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable bigquery.googleapis.com
   ```

2. **Authentication**:
   ```bash
   gcloud auth application-default login
   ```

3. **Permissions**: Service account or user needs:
   - `roles/aiplatform.admin` (to create agents)
   - `roles/bigquery.dataViewer` (to access BigQuery)
   - `roles/bigquery.jobUser` (to run queries)

4. **Dependencies**: Ensure `requests` is installed:
   ```bash
   pip install requests
   ```

#### Troubleshooting API Deployment

If the script fails, it will provide detailed error messages and alternatives:

1. **404 Errors**: The API endpoint structure may differ. The script tries multiple endpoints automatically.

2. **400 Errors**: Payload format may be incorrect. The script tries multiple formats.

3. **Authentication Errors**: Verify ADC is set up:
   ```bash
   gcloud auth application-default login
   ```

4. **Permission Errors**: Check IAM roles:
   ```bash
   gcloud projects get-iam-policy YOUR_PROJECT_ID
   ```

#### Manual API Approach (Alternative)

If the automated script doesn't work, you can use the Vertex AI REST API directly:

```python
from google.auth import default
from google.auth.transport.requests import Request
import requests

credentials, _ = default()
credentials.refresh(Request())

url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/us-central1/agents"
headers = {
    "Authorization": f"Bearer {credentials.token}",
    "Content-Type": "application/json",
}
payload = {
    "displayName": "bq_agent_mick",
    "description": "BigQuery agent",
    "instructions": "...",
    "model": "gemini-2.5-flash",
}

response = requests.post(url, headers=headers, json=payload)
```

See the script source code (`deploy_vertex_api.py`) for the complete implementation.

### Option D: Run Locally (Development)

For development and testing, simply run locally:

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from bq_agent_mick.agent import root_agent

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="local_test",
    session_service=session_service,
)

# Use runner as shown in main.py
```

## Security Considerations

1. **IAM Roles**: Ensure service accounts have:
   - `roles/aiplatform.user`
   - `roles/bigquery.dataViewer`
   - `roles/bigquery.jobUser`

2. **Write Mode**: Consider adding write blocking:
   ```python
   from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
   tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
   ```

3. **Cloud Run**: Use authentication and IAM for Cloud Run services

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure dependencies are installed
2. **Credentials**: Verify ADC or service account setup
3. **BigQuery Permissions**: Check IAM roles
4. **API Enablement**: Verify APIs are enabled

### Check Logs

View Cloud Run logs:
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

## Additional Resources

- [Vertex AI Agent Builder Documentation](https://cloud.google.com/vertex-ai/docs/agents)
- [Google ADK Documentation](https://cloud.google.com/python/docs/reference/adk)
- [Cloud Run Deployment](https://cloud.google.com/run/docs/deploying)
- [BigQuery IAM Roles](https://cloud.google.com/bigquery/docs/access-control)
