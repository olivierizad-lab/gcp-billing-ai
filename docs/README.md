# Deployment Scripts - IAP + Load Balancer

Complete deployment scripts for the Agent Engine Chat interface with IAP (Identity-Aware Proxy) and load balancer, based on the provisioner project pattern.

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

### Option 1: Deploy Everything at Once

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
export DOMAIN="agent-engine.yourdomain.com"
./deploy-all.sh
```

### Option 2: Deploy Step by Step

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
```

## What Gets Created

### Infrastructure (01-infrastructure.sh)
- ✅ VPC Network
- ✅ Subnet
- ✅ VPC Connector
- ✅ Service Accounts (API and UI)
- ✅ Global IP Address
- ✅ SSL Certificate

### IAM Permissions (02-iam-permissions.sh)
- ✅ API Service Account permissions (BigQuery, Vertex AI, Logging)
- ✅ Frontend Service Account permissions
- ✅ Cloud Build permissions

### Applications (03-applications.sh)
- ✅ Backend API Cloud Run service
- ✅ Frontend UI Cloud Run service
- ✅ Both configured for load balancer ingress only
- ✅ Both configured with no public access (IAP required)

### Load Balancer (04-load-balancer.sh)
- ✅ Network Endpoint Groups (NEGs)
- ✅ Backend Services
- ✅ URL Map with API routing (/api/* → backend)
- ✅ HTTPS Proxy
- ✅ Forwarding Rule
- ✅ IAP enabled on both backend services

## Post-Deployment Steps

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

Grant IAP access to users or groups:

```bash
# Grant access to a specific user
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=agent-engine-api-backend \
  --member='user:user@example.com' \
  --role='roles/iap.httpsResourceAccessor' \
  --project=YOUR_PROJECT_ID

# Grant access to all authenticated users
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

To remove everything (in reverse order):

```bash
# 4. Delete load balancer
gcloud compute forwarding-rules delete agent-engine-forwarding-rule --global --project=YOUR_PROJECT_ID
gcloud compute target-https-proxies delete agent-engine-proxy --global --project=YOUR_PROJECT_ID
gcloud compute url-maps delete agent-engine-url-map --global --project=YOUR_PROJECT_ID
gcloud compute backend-services delete agent-engine-api-backend --global --project=YOUR_PROJECT_ID
gcloud compute backend-services delete agent-engine-ui-backend --global --project=YOUR_PROJECT_ID
gcloud compute network-endpoint-groups delete agent-engine-api-neg --region=us-central1 --project=YOUR_PROJECT_ID
gcloud compute network-endpoint-groups delete agent-engine-ui-neg --region=us-central1 --project=YOUR_PROJECT_ID

# 3. Delete Cloud Run services
gcloud run services delete agent-engine-api --region=us-central1 --project=YOUR_PROJECT_ID
gcloud run services delete agent-engine-ui --region=us-central1 --project=YOUR_PROJECT_ID

# 1. Delete infrastructure
gcloud compute addresses delete agent-engine-lb-ip --global --project=YOUR_PROJECT_ID
gcloud compute ssl-certificates delete agent-engine-ssl-cert --global --project=YOUR_PROJECT_ID
gcloud vpc-access connectors delete agent-engine-vpc-connector --region=us-central1 --project=YOUR_PROJECT_ID
gcloud compute networks subnets delete agent-engine-subnet --region=us-central1 --project=YOUR_PROJECT_ID
gcloud compute networks delete agent-engine-vpc --project=YOUR_PROJECT_ID
```

## References

Based on the provisioner project deployment pattern:
- `provisioner/deploy/01-infrastructure.sh`
- `provisioner/deploy/04-load-balancer.sh`

