# Backend Deployment to Cloud Run

Deploy the FastAPI backend to Google Cloud Run.

## Prerequisites

```bash
# Install gcloud CLI (if not already installed)
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

## Step 1: Create Dockerfile

Create `web/backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY ../bq_agent_mick ./bq_agent_mick
COPY ../bq_agent ./bq_agent
COPY ../.env* ./

# Cloud Run expects PORT environment variable
ENV PORT=8080
EXPOSE 8080

# Run the application
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
```

## Step 2: Update main.py for Cloud Run

Update the CORS configuration to allow your frontend domain:

```python
# In web/backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://YOUR-FRONTEND-DOMAIN.run.app",  # Cloud Run frontend
        "https://YOUR-FRONTEND-DOMAIN.web.app",  # Firebase Hosting
        "http://localhost:3000",  # Local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 3: Deploy to Cloud Run

```bash
cd web/backend

# Deploy (unauthenticated - for testing)
gcloud run deploy agent-engine-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=YOUR_PROJECT_ID,LOCATION=us-central1

# Or deploy with authentication (recommended for production)
gcloud run deploy agent-engine-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID=YOUR_PROJECT_ID,LOCATION=us-central1
```

## Step 4: Get Service URL

After deployment, you'll get a URL like:
```
https://agent-engine-api-xxxxx-uc.a.run.app
```

## Step 5: Configure Environment Variables

Set agent Reasoning Engine IDs as environment variables:

```bash
# Get your Reasoning Engine IDs
make list-deployments AGENT_NAME=bq_agent_mick

# Update Cloud Run service with env vars
gcloud run services update agent-engine-api \
  --region us-central1 \
  --update-env-vars \
    BQ_AGENT_MICK_REASONING_ENGINE_ID=your_id_here,\
    BQ_AGENT_REASONING_ENGINE_ID=your_id_here
```

Or set them during deployment:

```bash
gcloud run deploy agent-engine-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars \
    PROJECT_ID=YOUR_PROJECT_ID,\
    LOCATION=us-central1,\
    BQ_AGENT_MICK_REASONING_ENGINE_ID=your_id_here,\
    BQ_AGENT_REASONING_ENGINE_ID=your_id_here
```

## Step 6: Test the Deployment

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe agent-engine-api \
  --region us-central1 \
  --format 'value(status.url)')

# Test health endpoint
curl ${SERVICE_URL}/health

# Test agents endpoint
curl ${SERVICE_URL}/agents

# Test query (if unauthenticated)
curl -X POST ${SERVICE_URL}/query \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "bq_agent_mick",
    "message": "What are the top 5 services by cost?",
    "user_id": "test_user"
  }'
```

## Step 7: Authentication (Production)

### Option A: IAM Authentication (Recommended)

```bash
# Deploy with authentication
gcloud run deploy agent-engine-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated

# Grant access to specific users
gcloud run services add-iam-policy-binding agent-engine-api \
  --region us-central1 \
  --member="user:user@example.com" \
  --role="roles/run.invoker"

# Or grant to all authenticated users
gcloud run services add-iam-policy-binding agent-engine-api \
  --region us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

Then update your frontend to include auth tokens (see SECURITY.md).

### Option B: API Key Authentication

Add API key middleware to `main.py` (see SECURITY.md for implementation).

## Step 8: Monitor and Logs

```bash
# View logs
gcloud run services logs read agent-engine-api \
  --region us-central1 \
  --limit 50

# Monitor in Console
# https://console.cloud.google.com/run/detail/us-central1/agent-engine-api/metrics
```

## Troubleshooting

### "Permission denied" errors

Make sure the Cloud Run service account has permissions:
```bash
# Grant BigQuery permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

### CORS errors

Update CORS configuration in `main.py` to include your frontend domain.

### "Agent not configured" errors

Verify environment variables are set correctly:
```bash
gcloud run services describe agent-engine-api \
  --region us-central1 \
  --format 'value(spec.template.spec.containers[0].env)'
```

