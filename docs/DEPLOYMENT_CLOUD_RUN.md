# Cloud Run Deployment Guide - GCP Billing Agent

Complete guide for deploying the GCP Billing Agent to Google Cloud Run with IAP security.

## Overview

This guide covers deploying both the backend (FastAPI) and frontend (React) to Cloud Run services with:
- ✅ **IAP Authentication** - Secure access with Google accounts
- ✅ **HTTPS** - Automatic SSL/TLS encryption
- ✅ **Scalable** - Auto-scales based on traffic
- ✅ **Cost-effective** - Pay only for what you use

## Prerequisites

1. **GCP Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Required APIs enabled**:
   - Cloud Run API
   - Cloud Build API
   - IAM API
   - Container Registry API (or Artifact Registry)

## Quick Start

### Option 1: Simple IAP Deployment (No DNS Required)

Perfect for testing or quick deployments:

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
export REGION="us-central1"
./deploy-simple-iap.sh
```

This will:
- Create service accounts
- Build and deploy backend to Cloud Run
- Build and deploy frontend to Cloud Run
- Enable IAP authentication
- Provide you with `.run.app` URLs

### Option 2: Full Deployment with Load Balancer (Custom Domain)

For production with custom domain:

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export DOMAIN="agent-engine.innovationbox.cloud"
./deploy-all.sh
```

## Step-by-Step Deployment

### 1. Set Environment Variables

```bash
export PROJECT_ID="qwiklabs-asl-04-8e9f23e85ced"
export REGION="us-central1"
export DOMAIN="agent-engine.innovationbox.cloud"  # Optional, for load balancer
```

### 2. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  iam.googleapis.com \
  containerregistry.googleapis.com \
  --project="$PROJECT_ID"
```

### 3. Deploy Infrastructure

```bash
cd web/deploy
./01-infrastructure.sh
```

This creates:
- VPC network (if needed)
- Service accounts (API and Frontend)
- VPC connector (optional, for private networking)

### 4. Set Up IAM Permissions

```bash
./02-iam-permissions.sh
```

This grants:
- BigQuery permissions to API service account
- Vertex AI permissions to API service account
- Cloud Run invoker permissions

### 5. Deploy Applications

#### Option A: Simple IAP (Recommended for testing)

```bash
./03-applications-iap.sh
```

This deploys with:
- Native Cloud Run IAP
- No load balancer needed
- Uses `.run.app` URLs

#### Option B: With Load Balancer (For custom domain)

```bash
./03-applications.sh
./04-load-balancer.sh
```

This deploys with:
- Load balancer
- Custom domain support
- SSL certificate

### 6. Configure Frontend API URL

After deployment, update the frontend to use the backend URL:

**For Simple IAP:**
```bash
# Get the API URL
API_URL=$(gcloud run services describe agent-engine-api \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(status.url)")

# Update frontend environment or rebuild with API URL
```

**For Load Balancer:**
```bash
# Use the load balancer domain
API_URL="https://agent-engine.innovationbox.cloud/api"
```

### 7. Grant IAP Access

**Recommended: Use domain restrictions** (works immediately, no OAuth consent screen needed):

```bash
# Option 1: Domain restriction (Recommended for Google Workspace/Cloud Identity)
make security-harden \
  PROJECT_ID="$PROJECT_ID" \
  ACCESS_CONTROL_TYPE=domain \
  ACCESS_CONTROL_VALUE=your-domain.com

# Option 2: Manual domain restriction
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region="$REGION" \
  --member="domain:your-domain.com" \
  --role="roles/run.invoker" \
  --project="$PROJECT_ID"

gcloud run services add-iam-policy-binding agent-engine-api \
  --region="$REGION" \
  --member="domain:your-domain.com" \
  --role="roles/run.invoker" \
  --project="$PROJECT_ID"
```

**Alternative: All authenticated users** (requires OAuth consent screen configuration):

```bash
# Grant to all authenticated users (requires OAuth consent screen)
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region="$REGION" \
  --member="allAuthenticatedUsers" \
  --role="roles/run.invoker" \
  --project="$PROJECT_ID"

# See docs/AUTHENTICATION_SETUP.md for OAuth consent screen configuration
```

**For testing only (public access):**

```bash
# ⚠️ NOT SECURE - Use only for testing
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region="$REGION" \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --project="$PROJECT_ID"
```

## Configuration

### Backend Configuration

The backend needs:
- Agent `.env` files with `REASONING_ENGINE_ID`
- Access to BigQuery and Vertex AI
- Firestore for history (optional)

**Agent Configuration:**
The backend reads agent configs from:
- `bq_agent_mick/.env` - For bq_agent_mick
- `bq_agent/.env` - For bq_agent

Make sure these files exist in the Docker image (they're copied in the Dockerfile).

### Frontend Configuration

The frontend needs to know the backend API URL. The deployment scripts handle this automatically, but if you need to rebuild manually:

1. **Using Cloud Build (Recommended):**
   ```bash
   cd web/frontend
   gcloud builds submit --config=cloudbuild.yaml \
     --substitutions=_API_URL="https://api-url.run.app" \
     . --project="$PROJECT_ID"
   ```
   
   The `cloudbuild.yaml` and `Dockerfile` are configured to pass `VITE_API_URL` as a build argument.

2. **Manual build:**
   ```bash
   export VITE_API_URL="https://api-url.run.app"
   npm run build
   ```

**Important:** The Dockerfile uses a build argument (`ARG VITE_API_URL`) to ensure the API URL is embedded at build time. This is required because Vite environment variables are compiled into the JavaScript bundle.

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
2. You should be redirected to Google login
3. After authentication, you should see the chat interface

### 3. Configure Agents

Ensure your agents are deployed and configured:

```bash
# List agent deployments
make list-deployments AGENT_NAME=bq_agent_mick

# Verify agent IDs are in .env files
cat bq_agent_mick/.env
```

### 4. Update Frontend API URL

The deployment script (`03-applications-iap.sh`) automatically handles this by:
1. Getting the deployed API URL
2. Building the frontend with the API URL using Cloud Build substitutions
3. Configuring CORS on the backend to allow the frontend URL

If you need to rebuild manually:
```bash
cd web/frontend
API_URL="https://agent-engine-api-xxxxx.run.app"
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=_API_URL="$API_URL" \
  . --project="$PROJECT_ID"
  
# Then redeploy
gcloud run deploy agent-engine-ui \
  --image="gcr.io/$PROJECT_ID/agent-engine-ui:latest" \
  --region="$REGION" \
  --project="$PROJECT_ID"
```

## Troubleshooting

### Services Not Accessible

**Check IAP is enabled:**
```bash
gcloud run services describe agent-engine-ui \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(spec.template.spec.serviceAccountName)"
```

**Check IAM bindings:**
```bash
gcloud run services get-iam-policy agent-engine-ui \
  --region="$REGION" \
  --project="$PROJECT_ID"
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

**Firestore Permissions (if history saving fails):**
If you see "403 Missing or insufficient permissions" when saving query history:
```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:agent-engine-api-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

### Frontend Can't Connect to Backend

**Check CORS configuration:**
- Backend CORS should allow the frontend URL
- Check `main.py` CORS settings
- Verify `CORS_ALLOWED_ORIGINS` environment variable is set on the backend:
  ```bash
  gcloud run services describe agent-engine-api \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(spec.template.spec.containers[0].env)"
  ```

**Verify API URL is embedded in frontend:**
- The frontend JavaScript should contain the Cloud Run API URL, not `localhost:8000`
- Check browser console for errors
- Do a hard refresh (`Cmd+Shift+R` or `Ctrl+Shift+R`) to clear cached JavaScript
- If still seeing localhost, the build may not have embedded the API URL correctly
- Verify the Dockerfile receives `VITE_API_URL` as a build argument

## Cleanup

To remove all deployed resources:

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
./cleanup.sh
```

Or manually:
```bash
# Delete Cloud Run services
gcloud run services delete agent-engine-api --region="$REGION" --project="$PROJECT_ID"
gcloud run services delete agent-engine-ui --region="$REGION" --project="$PROJECT_ID"

# Delete service accounts
gcloud iam service-accounts delete agent-engine-api-sa@$PROJECT_ID.iam.gserviceaccount.com
gcloud iam service-accounts delete agent-engine-ui-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## Next Steps

- **Configure DNS** (if using load balancer): Point domain to load balancer IP
- **Grant access**: Configure IAP access policies for your users
- **Monitor**: Set up Cloud Monitoring and Logging
- **Scale**: Adjust min/max instances based on traffic

## References

- [GEN_AI_SOLUTION.md](./GEN_AI_SOLUTION.md) - Complete solution documentation
- [IAP_DEPLOYMENT.md](./IAP_DEPLOYMENT.md) - Detailed IAP deployment guide
- [DEPLOYMENT_SIMPLE.md](./DEPLOYMENT_SIMPLE.md) - Simple deployment guide

