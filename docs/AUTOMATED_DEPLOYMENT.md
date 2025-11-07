# Fully Automated Deployment Guide

## Overview

This guide covers the **fully automated deployment** that handles everything:
- ✅ Infrastructure setup (service accounts, Firestore)
- ✅ IAM permissions (custom roles, bindings)
- ✅ Security hardening (Cloud Identity access control)
- ✅ Application deployment (Cloud Run services)
- ✅ All in one command!

Perfect for **forking the repo** and deploying to your organization (e.g., `innovationbox.cloud`).

## Quick Start

### One Command Deployment

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Optional: Customize access control (defaults to domain: innovationbox.cloud)
export ACCESS_CONTROL_TYPE="domain"  # domain, group, users, or allAuthenticatedUsers
export ACCESS_CONTROL_VALUE="innovationbox.cloud"  # Your domain or group

# Deploy everything
cd web/deploy
./deploy-all-automated.sh
```

Or using Make:

```bash
make deploy-all-automated \
  PROJECT_ID=your-project-id \
  ACCESS_CONTROL_TYPE=domain \
  ACCESS_CONTROL_VALUE=innovationbox.cloud
```

### Skip Confirmation

```bash
./deploy-all-automated.sh -y
```

## What Gets Automated

### 1. APIs Enabled
- Cloud Run API
- Cloud Build API
- IAM API
- Firestore API
- BigQuery API
- Vertex AI API
- Logging API
- Monitoring API

### 2. Service Accounts Created
- `agent-engine-api-sa` - Backend API service account
- `agent-engine-ui-sa` - Frontend UI service account

### 3. Firestore Database
- Creates Firestore database in specified region
- Handles cases where it already exists

### 4. Custom IAM Role
- Creates `gcpBillingAgentService` custom role
- Includes only required permissions (least privilege)
- Updates if already exists

### 5. IAM Permissions
- Grants custom role to API service account
- Grants Cloud Build permissions
- Grants service account user permissions
- Removes old over-privileged roles

### 6. Application Deployment
- Builds and deploys backend API to Cloud Run
- Builds and deploys frontend UI to Cloud Run
- Configures CORS automatically
- Sets environment variables

### 7. Security Hardening
- Replaces `allAuthenticatedUsers` with domain/group/user restrictions
- Configures Cloud Identity-based access control
- Applies least privilege IAM

## Configuration Options

### Access Control Types

#### Domain-Level (Recommended)
Restrict to users in your organization:
```bash
export ACCESS_CONTROL_TYPE="domain"
export ACCESS_CONTROL_VALUE="innovationbox.cloud"
```

#### Group-Based
Use Cloud Identity groups:
```bash
export ACCESS_CONTROL_TYPE="group"
export ACCESS_CONTROL_VALUE="billing-users@innovationbox.cloud"
```

#### Individual Users
Grant to specific users:
```bash
export ACCESS_CONTROL_TYPE="users"
export ACCESS_CONTROL_VALUE="user1@innovationbox.cloud,user2@innovationbox.cloud"
```

#### All Authenticated Users (Less Secure)
For testing only:
```bash
export ACCESS_CONTROL_TYPE="allAuthenticatedUsers"
```

## Environment Variables

### Required
- `PROJECT_ID` - Your GCP project ID

### Optional
- `REGION` - GCP region (default: `us-central1`)
- `DOMAIN` - Domain for SSL certificates (default: `innovationbox.cloud`)
- `ACCESS_CONTROL_TYPE` - Access control type (default: `domain`)
- `ACCESS_CONTROL_VALUE` - Access control value (default: `innovationbox.cloud`)

## Example: Full Deployment for innovationbox.cloud

```bash
# Set project
export PROJECT_ID="your-innovationbox-project-id"

# Set domain and access control
export DOMAIN="innovationbox.cloud"
export ACCESS_CONTROL_TYPE="domain"
export ACCESS_CONTROL_VALUE="innovationbox.cloud"

# Deploy everything
cd web/deploy
./deploy-all-automated.sh -y
```

## Post-Deployment Steps

### 1. Deploy Agents

Deploy your agents to Vertex AI Agent Engine:

```bash
# Deploy bq_agent_mick
make deploy-agent-engine \
  PROJECT_ID=your-project-id \
  AGENT_DIR=bq_agent_mick \
  AGENT_NAME=bq_agent_mick

# Get the Reasoning Engine ID
make list-deployments \
  PROJECT_ID=your-project-id \
  AGENT_NAME=bq_agent_mick
```

### 2. Update Environment Variables

Update `bq_agent_mick/.env` with the Reasoning Engine ID:

```bash
# Get the Reasoning Engine ID from the deployment
REASONING_ENGINE_ID=$(gcloud ai reasoning-engines list \
  --project=your-project-id \
  --region=us-central1 \
  --filter="displayName:bq_agent_mick" \
  --format="value(name)" | head -1)

# Update .env file
echo "REASONING_ENGINE_ID=$REASONING_ENGINE_ID" >> bq_agent_mick/.env
```

### 3. Redeploy Backend (if needed)

If you updated the Reasoning Engine ID, redeploy the backend:

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
./03-applications.sh
```

### 4. Test Access

1. Open the UI URL in a browser
2. Authenticate with your Google account
3. Test querying your billing data

## Troubleshooting

### Firestore Database Creation Fails

If Firestore creation fails:
```bash
# Manually create Firestore database
gcloud firestore databases create \
  --location=us-central1 \
  --type=firestore-native \
  --project=PROJECT_ID
```

### Service Account Already Exists

The script handles this automatically - it will skip creation if the service account already exists.

### Custom Role Already Exists

The script will update the existing role instead of creating a new one.

### Access Denied After Deployment

If users can't access:
1. Check IAM policy:
   ```bash
   gcloud run services get-iam-policy agent-engine-ui \
     --region=us-central1 \
     --project=PROJECT_ID
   ```
2. Verify user's email matches the access control setting
3. Check Cloud Run logs for authentication errors

## Rollback

If you need to rollback to `allAuthenticatedUsers`:

```bash
export PROJECT_ID="your-project-id"
export ACCESS_CONTROL_TYPE="allAuthenticatedUsers"
cd web/deploy
./05-security-hardening.sh
```

## Cleanup

To remove all resources:

```bash
# Delete Cloud Run services
gcloud run services delete agent-engine-api --region=us-central1 --project=PROJECT_ID
gcloud run services delete agent-engine-ui --region=us-central1 --project=PROJECT_ID

# Delete service accounts
gcloud iam service-accounts delete agent-engine-api-sa@PROJECT_ID.iam.gserviceaccount.com
gcloud iam service-accounts delete agent-engine-ui-sa@PROJECT_ID.iam.gserviceaccount.com

# Delete custom IAM role
gcloud iam roles delete gcpBillingAgentService --project=PROJECT_ID
```

## Security Best Practices

1. **Use Domain or Group Access**: Avoid `allAuthenticatedUsers` in production
2. **Review Custom Role**: Ensure it has only required permissions
3. **Monitor Access**: Check Cloud Audit Logs regularly
4. **Rotate Secrets**: Update service account keys periodically
5. **Enable Monitoring**: Set up alerts for unusual access patterns

## Next Steps

After deployment:
- ✅ Set up Cloud Monitoring alerts
- ✅ Configure Cloud Audit Logs
- ✅ Review IAM permissions
- ✅ Test with real users
- ✅ Set up CI/CD for updates

## References

- [SECURITY_IMPROVEMENTS.md](./SECURITY_IMPROVEMENTS.md) - Security details
- [SECURITY_QUICK_REFERENCE.md](./SECURITY_QUICK_REFERENCE.md) - Quick security guide
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Detailed deployment guide for Cloud Run & Agent Engine

