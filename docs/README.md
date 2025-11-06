# Documentation Index - GCP Billing Agent

This directory contains all project documentation for the GCP Billing Agent Gen AI solution.

## 📚 Documentation Structure

### Getting Started
- **[START_HERE.md](./START_HERE.md)** - Entry point and overview (start here!)
- **[GETTING_STARTED.md](./GETTING_STARTED.md)** - Detailed local development and deployment guide
- **[QUICKSTART.md](./QUICKSTART.md)** - 5-minute local development quick start
- **[QUICK_START.md](./QUICK_START.md)** - Quick deployment guide for Cloud Run

### Comprehensive Guides
- **[GEN_AI_SOLUTION.md](./GEN_AI_SOLUTION.md)** - Complete solution documentation (architecture, features, API, troubleshooting)

### Deployment Guides
- **[DEPLOYMENT_CLOUD_RUN.md](./DEPLOYMENT_CLOUD_RUN.md)** - Complete Cloud Run deployment guide (recommended for advanced users)
- **[AUTOMATED_DEPLOYMENT.md](./AUTOMATED_DEPLOYMENT.md)** - Fully automated deployment with load balancer and custom domain
- **[DEPLOYMENT_SIMPLE.md](./DEPLOYMENT_SIMPLE.md)** - Simple IAP deployment (no DNS or load balancer required)
- **[IAP_DEPLOYMENT.md](./IAP_DEPLOYMENT.md)** - IAP (Identity-Aware Proxy) deployment guide
- **[DEPLOYMENT_FAQ.md](./DEPLOYMENT_FAQ.md)** - Common deployment questions and answers

### Specialized Topics
- **[TESTING_HISTORY.md](./TESTING_HISTORY.md)** - Testing the Firestore history feature
- **[SECURITY.md](./SECURITY.md)** - Security considerations and best practices
- **[AUTHENTICATION_SETUP.md](./AUTHENTICATION_SETUP.md)** - Authentication setup guide (recommended: domain restrictions)
- **[SECURITY_IMPROVEMENTS.md](./SECURITY_IMPROVEMENTS.md)** - Security improvement plan and implementation
- **[DEPLOYMENT_FAQ.md](./DEPLOYMENT_FAQ.md)** - Common deployment questions and answers

### Agent Documentation
- **[agents/](./agents/)** - Agent-specific documentation
  - `bq_agent_mick.md` - bq_agent_mick agent documentation
  - `bq_agent_mick_deployment.md` - Deployment guide
  - `bq_agent_mick_usage.md` - Usage guide
  - `session_management.md` - Session management for Agent Engine

---

## 🚀 Quick Navigation

**New to the project?** Start with [START_HERE.md](./START_HERE.md) or [GETTING_STARTED.md](./GETTING_STARTED.md)

**Want to deploy?** Check [DEPLOYMENT_SIMPLE.md](./DEPLOYMENT_SIMPLE.md) for the easiest deployment option

**Need comprehensive info?** See [GEN_AI_SOLUTION.md](./GEN_AI_SOLUTION.md)

**Troubleshooting?** Check [GEN_AI_SOLUTION.md](./GEN_AI_SOLUTION.md) troubleshooting section or [DEPLOYMENT_FAQ.md](./DEPLOYMENT_FAQ.md)

---

## Deployment Scripts - IAP + Load Balancer

Complete deployment scripts for the GCP Billing Agent interface with IAP (Identity-Aware Proxy) and load balancer, based on the provisioner project pattern.

## Architecture

```
Internet
   ↓
Load Balancer (HTTPS + IAP)
   ↓
├─→ /api/* → Backend Service → API NEG → Cloud Run API
└─→ /* → Frontend Service → UI NEG → Cloud Run UI
```

## Prerequisites

1. **GCP Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Domain** (for SSL certificate)
4. **Docker** (for building images)

## Configuration

Update these variables in the scripts or export them:

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export DOMAIN="agent-engine.yourdomain.com"
```

Or edit the scripts directly (they have defaults).

## Quick Start

### Option 1: Fully Automated Deployment (Recommended)

This option deploys the entire application stack (infrastructure, IAM, backend, frontend, security hardening) with a single command. It sets up a load balancer with IAP and a custom domain.

```bash
make deploy-web-automated PROJECT_ID="your-project-id" DOMAIN="agent-engine.yourdomain.com" ACCESS_CONTROL_TYPE=domain ACCESS_CONTROL_VALUE=your-domain.com
```

### Option 2: Simple IAP Deployment

This option deploys the backend and frontend to Cloud Run with native IAP support. No load balancer or custom domain is required.

```bash
make deploy-web-simple PROJECT_ID="your-project-id"
```

### Option 3: Step-by-Step Deployment (Advanced)

For more control, you can run the individual deployment scripts located in `web/deploy/`:

```bash
cd web/deploy

# 1. Infrastructure (VPC, SSL, IP, Service Accounts)
export PROJECT_ID="your-project-id"
export DOMAIN="agent-engine.yourdomain.com"
./01-infrastructure.sh

# 2. IAM Permissions
./02-iam-permissions.sh

# 3. Deploy Applications (Cloud Run)
export REGION="us-central1"
./03-applications.sh

# 4. Load Balancer + IAP
./04-load-balancer.sh

# 5. Security Hardening
export ACCESS_CONTROL_TYPE=domain
export ACCESS_CONTROL_VALUE=your-domain.com
./05-security-hardening.sh

# 6. Configure Authentication
./06-configure-authentication.sh

# 7. Verify Deployment
./verify-deployment.sh
```

## What Gets Created (Automated Deployment)

### Infrastructure (via `01-infrastructure.sh`)
- ✅ VPC Network
- ✅ Subnet
- ✅ VPC Connector
- ✅ Service Accounts (API and UI)
- ✅ Global IP Address
- ✅ SSL Certificate
- ✅ Firestore Database

### IAM Permissions (via `02-iam-permissions.sh`)
- ✅ Custom IAM Role (`gcpBillingAgentService`)
- ✅ API Service Account permissions (BigQuery, Vertex AI, Logging, Firestore)
- ✅ Frontend Service Account permissions
- ✅ Cloud Build permissions

### Applications (via `03-applications.sh` or `03-applications-iap.sh`)
- ✅ Backend API Cloud Run service
- ✅ Frontend UI Cloud Run service
- ✅ Both configured for load balancer ingress only (automated) or native IAP (simple)
- ✅ Both configured with no public access (IAP required)

### Load Balancer (via `04-load-balancer.sh` - Automated Deployment Only)
- ✅ Network Endpoint Groups (NEGs)
- ✅ Backend Services
- ✅ URL Map with API routing (/api/* → backend)
- ✅ HTTPS Proxy
- ✅ Forwarding Rule
- ✅ IAP enabled on both backend services

### Security Hardening (via `05-security-hardening.sh`)
- ✅ Cloud Run services restricted to specified domain/group/users

### Authentication Configuration (via `06-configure-authentication.sh`)
- ✅ OAuth Consent Screen configuration (requires manual steps for external users)
- ✅ IAP enabled on backend services

## Post-Deployment Steps (Automated Deployment)

### 1. Configure DNS

Point your domain to the load balancer IP:

```bash
# Get the load balancer IP
gcloud compute addresses describe agent-engine-lb-ip \
  --global \
  --project=YOUR_PROJECT_ID \
  --format="value(address)"

# Configure DNS A record to point to this IP
```

### 2. Grant IAP Access

If you used `ACCESS_CONTROL_TYPE=allAuthenticatedUsers` or need to grant access to specific users/groups beyond the initial deployment configuration, use the following commands:

```bash
# Grant access to a specific user
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=agent-engine-api-backend \
  --member='user:user@example.com' \
  --role='roles/iap.httpsResourceAccessor' \
  --project=YOUR_PROJECT_ID

# Grant access to all authenticated users (if not already configured)
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=agent-engine-api-backend \
  --member='allAuthenticatedUsers' \
  --role='roles/iap.httpsResourceAccessor' \
  --project=YOUR_PROJECT_ID

# Repeat for UI backend
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=agent-engine-ui-backend \
  --member='allAuthenticatedUsers' \
  --role='roles/iap.httpsResourceAccessor' \
  --project=YOUR_PROJECT_ID
```

### 3. Update Frontend API URL

Update the frontend to use the load balancer domain:

```bash
# In web/frontend/.env.production or update vite.config.js
VITE_API_URL=https://agent-engine.yourdomain.com/api
```

Then rebuild and redeploy the frontend.

## Security Features

✅ **IAP Authentication** - Users authenticate with Google accounts  
✅ **No Public Access** - Services only accessible through load balancer  
✅ **HTTPS Only** - SSL/TLS encryption  
✅ **VPC Connector** - Private networking  
✅ **Service Account Isolation** - Separate service accounts for API and UI  

## Troubleshooting

### IAP Not Working

1. Check IAP is enabled:
   ```bash
   gcloud compute backend-services describe agent-engine-api-backend \
     --global \
     --project=YOUR_PROJECT_ID \
     --format="value(iap.enabled)"
   ```

2. Check IAP access policy:
   ```bash
   gcloud iap web get-iam-policy \
     --resource-type=backend-services \
     --service=agent-engine-api-backend \
     --project=YOUR_PROJECT_ID
   ```

### Services Not Accessible

1. Check Cloud Run ingress:
   ```bash
   gcloud run services describe agent-engine-api \
     --region=us-central1 \
     --project=YOUR_PROJECT_ID \
     --format="value(spec.template.metadata.annotations.'run.googleapis.com/ingress')"
   ```
   Should be: `internal-and-cloud-load-balancing`

2. Check NEGs:
   ```bash
   gcloud compute network-endpoint-groups list \
     --region=us-central1 \
     --project=YOUR_PROJECT_ID
   ```

### SSL Certificate Issues

1. Check certificate status:
   ```bash
   gcloud compute ssl-certificates describe agent-engine-ssl-cert \
     --global \
     --project=YOUR_PROJECT_ID
   ```

2. Verify DNS is configured correctly

## Idempotency

All scripts are **idempotent** - they can be run multiple times safely. They check if resources exist before creating them.

## Cleanup

To remove all resources created by the automated deployment, run:

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
./cleanup.sh
```

To remove resources created by the simple IAP deployment, you will need to manually delete the Cloud Run services and any associated service accounts.


