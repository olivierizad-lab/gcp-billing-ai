# Deployment Guide – Cloud Run & Agent Engine

Complete guide for deploying the GCP Billing Agent web app (frontend + backend on Cloud Run) and the reasoning agents running on Vertex AI Agent Engine.

## Architecture Snapshot

```
┌─────────────────────┐            ┌─────────────────────┐
│  React Frontend     │  HTTPS     │  FastAPI Backend    │
│  Cloud Run (nginx)  ├──────────▶ │  Cloud Run (Python) │
└──────────┬──────────┘            └──────────┬──────────┘
           │                                  │
           │                                  │ Vertex AI API
           │                                  ▼
           │                         ┌─────────────────────┐
           └────────────────────────▶│  Vertex AI Agent    │
                                     │  Engine (agents)    │
                                     └─────────────────────┘

Firestore stores users and query history. Cloud Build handles container builds.
```

## Why Cloud Run?

- **Serverless**: Scales to zero and back based on traffic
- **Managed security**: HTTPS, IAM integration, optional domain restrictions
- **Fast iteration**: Deployment scripts (`web/deploy/deploy-web.sh`) rebuild both services in minutes
- **Cost control**: Pay only for requests processed and execution time

Cloud Storage + Cloud CDN remains an alternative for the frontend, but Cloud Run keeps the authentication flow and deployment tooling consistent end to end.

## Agent Engine Deployment Overview

Vertex AI Agent Engine hosts the reasoning engines that power chat responses. Deploy agents with the ADK tooling, then let the backend auto-discover them at runtime.

```bash
# Example: deploy BigQuery agent with ADK
cd agents/bq_agent
adk deploy agent_engine \
  --project "$PROJECT_ID" \
  --location "$REGION" \
  --display-name "Billing Insights"

# List deployed reasoning engines
gcloud ai reasoning-engines list \
  --project="$PROJECT_ID" \
  --region="$REGION"
```

Key points:
- Agents are defined in the `agents/` directory (see `agents/bq_agent.md` for configuration specifics).
- No manual ID wiring is required—the backend scans Agent Engine at startup.
- If IAM restrictions block discovery, fall back to environment variables (`BQ_AGENT_REASONING_ENGINE_ID`, etc.) using the deployment script.

## Overview

This guide covers deploying both the backend (FastAPI) and frontend (React) to Cloud Run services with:
- ✅ **Firestore Authentication** - Custom JWT-based authentication with domain restrictions
- ✅ **HTTPS** - Automatic SSL/TLS encryption
- ✅ **Auto-scaling** - Scales based on traffic
- ✅ **Cost-effective** - Pay only for what you use
- ✅ **Auto-discovery** - Agents automatically discovered from Vertex AI Agent Engine

## Prerequisites

1. **GCP Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Required APIs enabled** (automated in deployment scripts):
   - Cloud Run API
   - Cloud Build API
   - IAM API
   - Container Registry API (or Artifact Registry)
   - Vertex AI API
   - Firestore API

## Quick Start

### Automated Deployment (Recommended)

Deploy everything with one command:

```bash
make deploy-web-simple PROJECT_ID=your-project-id
```

Or using the deployment script directly:

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
export REGION="us-central1"
./deploy-web.sh
```

This will:
- Enable required APIs
- Create service accounts with proper IAM roles
- Build and deploy backend to Cloud Run
- Build and deploy frontend to Cloud Run
- Configure Firestore authentication
- Auto-discover agents from Vertex AI Agent Engine

### Manual Deployment (advanced / custom builds)

Automation is preferred, but you can deploy individual services when testing Docker changes or experimenting with environment variables.

#### Backend (FastAPI) manual steps

```bash
cd web/backend

# Build image with Cloud Build
gcloud builds submit --tag="gcr.io/$PROJECT_ID/agent-engine-api"

# Deploy to Cloud Run
gcloud run deploy agent-engine-api \
  --image "gcr.io/$PROJECT_ID/agent-engine-api" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars \
    GCP_PROJECT_ID=$PROJECT_ID,\
    LOCATION=$REGION
```

You normally do **not** need to set agent IDs—auto-discovery handles it. Optional environment variables like `BQ_AGENT_REASONING_ENGINE_ID` act only as a fallback.

#### Frontend (React + nginx) manual steps

```bash
cd web/frontend
npm install
npm run build

gcloud builds submit --tag="gcr.io/$PROJECT_ID/agent-engine-ui"

gcloud run deploy agent-engine-ui \
  --image "gcr.io/$PROJECT_ID/agent-engine-ui" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars \
    VITE_API_URL="https://agent-engine-api-xxxxx-uc.a.run.app"
```

If you need to override documentation links, supply `VITE_GITBOOK_URL` during deployment or set `GITBOOK_URL` before running `deploy-web.sh`.

### What Gets Created

- ✅ **Service Accounts**:
  - `agent-engine-api-sa` - Backend service account
  - `agent-engine-ui-sa` - Frontend service account
- ✅ **Cloud Run Services**:
  - `agent-engine-api` - FastAPI backend
  - `agent-engine-ui` - React frontend
- ✅ **IAM Permissions**:
  - Custom role with minimal required permissions
  - BigQuery, Vertex AI, Firestore access
- ✅ **Firestore Collections**:
  - `users` - User accounts
  - `query_history` - Query history per user

## Deployment Details

### Step 1: Set Environment Variables

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
```

### Step 2: Run Automated Deployment

```bash
cd web/deploy
./deploy-web.sh
```

The script will:
1. Enable required APIs
2. Create service accounts
3. Set up IAM permissions
4. Build Docker images (Cloud Build)
5. Deploy backend service
6. Deploy frontend service
7. Configure environment variables
8. Set up CORS

### Step 3: Access the Application

After deployment, you'll get URLs like:
- **API**: `https://agent-engine-api-xxxxx-uc.a.run.app`
- **UI**: `https://agent-engine-ui-xxxxx-uc.a.run.app`

## Configuration

### Backend Configuration

The backend automatically:
- **Discovers agents** from Vertex AI Agent Engine (no manual configuration needed)
- **Uses Firestore** for user authentication and query history
- **Reads environment variables** for project configuration:
  - `BQ_PROJECT` or `GCP_PROJECT_ID` - GCP project ID
  - `LOCATION` - Region (default: `us-central1`)
  - `JWT_SECRET_KEY` - Secret key for JWT tokens (auto-generated)

### Frontend Configuration

The frontend:
- **Connects to backend** via API URL (automatically configured during build)
- **Uses JWT tokens** for authentication
- **Supports domain restrictions** (currently `@asl.apps-eval.com`)

### Agent Discovery

Agents are automatically discovered from Vertex AI Agent Engine:
- Backend scans for all reasoning engines on startup
- Cache refreshes every 5 minutes
- Fallback to environment variables if API scan fails
- No manual agent configuration needed

## Authentication

### Sign Up

1. Navigate to the UI URL
2. Click "Sign Up"
3. Enter email (must be from `@asl.apps-eval.com`)
4. Enter password
5. Account is created in Firestore

### Sign In

1. Navigate to the UI URL
2. Click "Sign In"
3. Enter email and password
4. JWT token is stored in browser
5. All API requests include the token

### Domain Restrictions

Currently restricted to `@asl.apps-eval.com` emails. To change:
1. Update `REQUIRED_DOMAIN` in `web/backend/auth.py`
2. Update `REQUIRED_DOMAIN` in `web/frontend/src/Auth.jsx`
3. Redeploy services

## Post-Deployment Steps

### 1. Verify Services

```bash
# List Cloud Run services
gcloud run services list --region="$REGION" --project="$PROJECT_ID"

# Check service details
gcloud run services describe agent-engine-api \
  --region="$REGION" \
  --project="$PROJECT_ID"
```

### 2. Test Access

1. Open the UI URL in a browser
2. Sign up with an `@asl.apps-eval.com` email
3. Sign in
4. Verify agents appear in the dropdown
5. Test a query

### 3. Verify Agent Discovery

Check logs to confirm agents are discovered:

```bash
gcloud run services logs read agent-engine-api \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --limit=50 | grep -i "agent"
```

Look for:
- `✓ Scanned Agent Engine: Found X reasoning engine(s)`
- `✓ Loaded X agent(s) from Agent Engine`

### 4. Grant Access (Optional)

By default, services are publicly accessible. To restrict:

```bash
# Restrict to specific domain
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region="$REGION" \
  --member="domain:your-domain.com" \
  --role="roles/run.invoker" \
  --project="$PROJECT_ID"

# Remove public access
gcloud run services remove-iam-policy-binding agent-engine-ui \
  --region="$REGION" \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --project="$PROJECT_ID"
```

## Troubleshooting

### Services Not Accessible

**Check IAM bindings:**
```bash
gcloud run services get-iam-policy agent-engine-ui \
  --region="$REGION" \
  --project="$PROJECT_ID"
```

**Check service account:**
```bash
gcloud run services describe agent-engine-api \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(spec.template.spec.serviceAccountName)"
```

### Backend Errors

**Check backend logs:**
```bash
gcloud run services logs read agent-engine-api \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --limit=50
```

**Verify service account permissions:**
```bash
gcloud projects get-iam-policy "$PROJECT_ID" \
  --flatten="bindings[].members" \
  --filter="bindings.members:agent-engine-api-sa@$PROJECT_ID.iam.gserviceaccount.com"
```

### Agent Discovery Not Working

**Check Vertex AI permissions:**
The service account needs `roles/aiplatform.user` or custom role with:
- `aiplatform.reasoningEngines.list`
- `aiplatform.reasoningEngines.get`
- `aiplatform.reasoningEngines.query`

**Check logs for errors:**
```bash
gcloud run services logs read agent-engine-api \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --limit=50 | grep -i "agent\|reasoning"
```

**Verify agents are deployed:**
```bash
python3 scripts/list_agent_engines.py \
  --project="$PROJECT_ID" \
  --location="$REGION"
```

### Frontend Can't Connect to Backend

**Check CORS configuration:**
- Backend CORS should allow the frontend URL
- Verify `CORS_ALLOWED_ORIGINS` includes frontend URL

**Verify API URL is embedded:**
- The frontend JavaScript should contain the Cloud Run API URL
- Check browser console for errors
- Do a hard refresh (`Cmd+Shift+R` or `Ctrl+Shift+R`)

**Check environment variables:**
```bash
gcloud run services describe agent-engine-api \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(spec.template.spec.containers[0].env)"
```

### Authentication Issues

**Check JWT secret key:**
- Must be the same across deployments
- Auto-generated and stored in Cloud Run environment variables

**Check Firestore permissions:**
- Service account needs `roles/datastore.user`
- Verify Firestore API is enabled

## FAQ

### Can the frontend live on Agent Engine?

No. Vertex AI Agent Engine only hosts reasoning engines and exposes REST endpoints. Keep the UI on Cloud Run (or Cloud Storage + CDN) and call Agent Engine through the FastAPI backend.

### Why split frontend and backend services?

Independent services let you redeploy without downtime, scale each tier separately, and keep resource usage efficient. A combined service is fine for prototypes but not required here.

### How is access controlled without IAP?

The backend enforces Firestore sign-in with domain restrictions and JWT tokens. Cloud Run defaults to HTTPS and you can tighten `roles/run.invoker` to your corporate domain if you need extra control.

### Do I need to manage agent IDs manually?

No. Auto-discovery queries Vertex AI Agent Engine on startup. Environment variables like `BQ_AGENT_REASONING_ENGINE_ID` are optional fallbacks for restricted environments.

### How do I point the UI at updated documentation?

Set `GITBOOK_URL` (or `VITE_GITBOOK_URL`) before deploying the frontend. The Dockerfile reads that value and bakes links into the bundle.

## Metrics Snapshot Pipeline (Cloud Run Job + Firestore)

The `/metrics` endpoint and UI dashboard now read from Firestore snapshots produced by a scheduled Cloud Run Job. This keeps expensive Git history analysis out of the request path and works inside Cloud Run's read-only filesystem.

### 1. Create a GitHub token (one-time)

1. In GitHub, visit **Settings → Developer settings → Personal access tokens (classic)**.
2. Generate a token with **repo (read)** scope only – this lets the collector query commit history.
3. Store it in Secret Manager (replace the project ID):

```bash
echo "ghp_..." | gcloud secrets create github-metrics-token \
  --replication-policy=automatic \
  --data-file=- \
  --project "$PROJECT_ID"

# Allow the collector job to read it (service account created in the next step)
gcloud secrets add-iam-policy-binding github-metrics-token \
  --member="serviceAccount:metrics-collector-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project "$PROJECT_ID"
```

### 2. Deploy the Cloud Run Job

Reuse the backend image but override the command to run `metrics_job.py`:

```bash
# 1) Create a dedicated service account (once)
gcloud iam service-accounts create metrics-collector-sa \
  --display-name="Metrics Collector" \
  --project "$PROJECT_ID"

# 2) Grant Firestore + Secret access
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:metrics-collector-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:metrics-collector-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3) Deploy the job (re-run after backend image updates)
#    The image below reuses the backend Cloud Run service image
API_SERVICE="agent-engine-api"
gcloud run jobs deploy metrics-collector \
  --image="gcr.io/$PROJECT_ID/$API_SERVICE:latest" \
  --region="$REGION" \
  --service-account="metrics-collector-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --command=python \
  --args=metrics_job.py \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,LOCATION=$REGION" \
  --set-secrets="GITHUB_TOKEN=github-metrics-token:latest" \
  --project "$PROJECT_ID"

# (Optional) customise analysis windows
# Add --set-env-vars="METRICS_WINDOWS=7,30,90" to limit which snapshots are collected.

# Run once to seed Firestore
gcloud run jobs execute metrics-collector \
  --region="$REGION" \
  --project "$PROJECT_ID"
```

The deploy command also runs the job once (`--execute-now`) so the dashboard has initial data.

### 3. Schedule recurring snapshots

Use Cloud Scheduler to execute the job every two hours:

```bash
gcloud scheduler jobs create http metrics-collector-schedule \
  --schedule="0 */2 * * *" \
  --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/metrics-collector:run" \
  --http-method=POST \
  --oauth-service-account-email="metrics-collector-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform" \
  --project "$PROJECT_ID"
```

### 4. Hook up the backend refresh endpoint

`deploy-web.sh` automatically injects `METRICS_JOB_NAME` if a job named `metrics-collector` exists in the deployment region. If you use a different job name, set the variable manually when deploying:

```bash
export METRICS_JOB_NAME="projects/$PROJECT_ID/locations/$REGION/jobs/custom-metrics-job"
make deploy-web-simple PROJECT_ID=$PROJECT_ID REGION=$REGION
```

The `/metrics/refresh` endpoint triggers the job on demand; the frontend now calls it before polling Firestore for the newest snapshot.

## Cleanup

To remove all deployed resources:

```bash
# Delete Cloud Run services
gcloud run services delete agent-engine-api \
  --region="$REGION" \
  --project="$PROJECT_ID"

gcloud run services delete agent-engine-ui \
  --region="$REGION" \
  --project="$PROJECT_ID"

# Delete service accounts (optional)
gcloud iam service-accounts delete agent-engine-api-sa@$PROJECT_ID.iam.gserviceaccount.com
gcloud iam service-accounts delete agent-engine-ui-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## Next Steps

- **Monitor**: Set up Cloud Monitoring and Logging
- **Scale**: Adjust min/max instances based on traffic
- **Customize**: Update domain restrictions for your organization
- **Deploy agents**: Deploy your agents to Vertex AI Agent Engine

## References

- [architecture.md](./architecture.md) - Complete system architecture
- [AUTOMATED_DEPLOYMENT.md](./AUTOMATED_DEPLOYMENT.md) - Automated deployment guide
- [AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md) - Authentication details
