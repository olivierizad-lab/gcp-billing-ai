# IAP + Load Balancer Deployment Guide

## Overview

This deployment uses **IAP (Identity-Aware Proxy)** and a **load balancer**, exactly like your provisioner project. This provides enterprise-grade security with Google authentication.

## Architecture

```
Internet
   ↓
Load Balancer (HTTPS + IAP)
   ↓
├─→ /api/* → Backend Service → API NEG → Cloud Run API
└─→ /* → Frontend Service → UI NEG → Cloud Run UI
```

## Quick Start

```bash
cd web/deploy

# Set configuration
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export DOMAIN="agent-engine.yourdomain.com"

# Deploy everything
./deploy-all.sh
```

## What Gets Created

### 1. Infrastructure
- VPC Network
- Subnet
- VPC Connector
- Service Accounts
- Global IP Address
- SSL Certificate

### 2. IAM Permissions
- API Service Account (BigQuery, Vertex AI)
- Frontend Service Account
- Cloud Build permissions

### 3. Cloud Run Services
- Backend API (internal-only, load balancer ingress)
- Frontend UI (internal-only, load balancer ingress)

### 4. Load Balancer + IAP
- Network Endpoint Groups (NEGs)
- Backend Services
- URL Map (routes /api/* to backend)
- HTTPS Proxy
- Forwarding Rule
- **IAP enabled** on both backend services

## Post-Deployment Steps

### 1. Configure DNS

Point your domain to the load balancer IP:

```bash
# Get IP
LB_IP=$(gcloud compute addresses describe agent-engine-lb-ip \
  --global \
  --project=$PROJECT_ID \
  --format="value(address)")

echo "Configure DNS A record: $DOMAIN → $LB_IP"
```

### 2. Grant IAP Access

**Grant access to users:**

```bash
# Specific user
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=agent-engine-api-backend \
  --member='user:user@example.com' \
  --role='roles/iap.httpsResourceAccessor' \
  --project=$PROJECT_ID

# All authenticated users
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=agent-engine-api-backend \
  --member='allAuthenticatedUsers' \
  --role='roles/iap.httpsResourceAccessor' \
  --project=$PROJECT_ID

# Repeat for UI backend
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=agent-engine-ui-backend \
  --member='allAuthenticatedUsers' \
  --role='roles/iap.httpsResourceAccessor' \
  --project=$PROJECT_ID
```

**Grant access to groups:**

```bash
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=agent-engine-api-backend \
  --member='group:security-team@example.com' \
  --role='roles/iap.httpsResourceAccessor' \
  --project=$PROJECT_ID
```

### 3. Update Frontend API URL

Update the frontend to use the load balancer domain:

```bash
# In web/frontend/.env.production
VITE_API_URL=https://agent-engine.yourdomain.com/api
```

Rebuild and redeploy frontend, or update the environment variable in Cloud Run.

## Security Features

✅ **IAP Authentication** - Users authenticate with Google accounts  
✅ **No Public Access** - Services only accessible through load balancer  
✅ **HTTPS Only** - SSL/TLS encryption  
✅ **VPC Connector** - Private networking  
✅ **Service Account Isolation** - Separate service accounts  

## How It Works

1. **User accesses** `https://agent-engine.yourdomain.com`
2. **Load balancer** routes request:
   - `/api/*` → Backend Service → API NEG → Cloud Run API
   - `/*` → Frontend Service → UI NEG → Cloud Run UI
3. **IAP checks** user authentication
4. **If authenticated**, request proceeds to Cloud Run service
5. **If not authenticated**, user is redirected to Google login

## Testing IAP

1. **Access the domain** (must be configured in DNS):
   ```
   https://agent-engine.yourdomain.com
   ```

2. **You should be redirected** to Google login if not authenticated

3. **After login**, you should see the ChatGCP interface

4. **Check IAP headers** in backend:
   ```python
   # IAP provides these headers:
   X-Goog-IAP-JWT-Assertion  # JWT token
   X-Goog-Authenticated-User-Email  # User email
   X-Goog-Authenticated-User-Id  # User ID
   ```

## Troubleshooting

### IAP Not Working

1. **Check IAP is enabled:**
   ```bash
   gcloud compute backend-services describe agent-engine-api-backend \
     --global \
     --project=$PROJECT_ID \
     --format="value(iap.enabled)"
   ```
   Should return: `True`

2. **Check IAP access policy:**
   ```bash
   gcloud iap web get-iam-policy \
     --resource-type=backend-services \
     --service=agent-engine-api-backend \
     --project=$PROJECT_ID
   ```

3. **Verify SSL certificate:**
   ```bash
   gcloud compute ssl-certificates describe agent-engine-ssl-cert \
     --global \
     --project=$PROJECT_ID
   ```

### Services Not Accessible

1. **Check Cloud Run ingress:**
   ```bash
   gcloud run services describe agent-engine-api \
     --region=us-central1 \
     --project=$PROJECT_ID \
     --format="value(spec.template.metadata.annotations.'run.googleapis.com/ingress')"
   ```
   Should be: `internal-and-cloud-load-balancing`

2. **Check NEGs:**
   ```bash
   gcloud compute network-endpoint-groups list \
     --region=us-central1 \
     --project=$PROJECT_ID
   ```

### DNS Not Working

1. **Verify DNS is configured:**
   ```bash
   dig $DOMAIN
   ```

2. **Check load balancer IP:**
   ```bash
   gcloud compute addresses describe agent-engine-lb-ip \
     --global \
     --project=$PROJECT_ID \
     --format="value(address)"
   ```

## Comparison with Provisioner Project

This deployment follows the **exact same pattern** as your provisioner project:

| Component | Provisioner | Agent Engine Chat |
|-----------|-------------|-------------------|
| **IAP** | ✅ | ✅ |
| **Load Balancer** | ✅ | ✅ |
| **NEGs** | ✅ | ✅ |
| **Backend Services** | ✅ | ✅ |
| **VPC Connector** | ✅ | ✅ |
| **SSL/TLS** | ✅ | ✅ |
| **Internal-only Cloud Run** | ✅ | ✅ |

## Scripts Reference

All scripts are in `web/deploy/`:
- `01-infrastructure.sh` - VPC, SSL, IP, Service Accounts
- `02-iam-permissions.sh` - IAM roles and permissions
- `03-applications.sh` - Cloud Run deployments
- `04-load-balancer.sh` - Load balancer + IAP setup
- `deploy-all.sh` - Runs all scripts in sequence

See [deploy/README.md](./deploy/README.md) for detailed documentation.

