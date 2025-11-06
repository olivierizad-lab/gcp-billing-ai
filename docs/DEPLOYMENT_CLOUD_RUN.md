# Cloud Run Deployment Guide - GCP Billing Agent

Complete guide for deploying the GCP Billing Agent to Google Cloud Run with Firestore authentication.

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
- [DEPLOYMENT_FAQ.md](./DEPLOYMENT_FAQ.md) - Common questions
