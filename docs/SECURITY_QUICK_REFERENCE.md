# Security Quick Reference - Answers to Your Questions

## Your Questions Answered

### 1. Can we use IAM and the users Cloud Identity account?

**Yes!** Here's how:

#### Option A: Domain-Level Access (Recommended)
Restrict access to users in your organization:
```bash
export ACCESS_CONTROL_TYPE="domain"
export ACCESS_CONTROL_VALUE="innovationbox.cloud"
./web/deploy/05-security-hardening.sh
```

This allows **any user** with an `@innovationbox.cloud` email address to access the app.

#### Option B: Group-Based Access (More Granular)
Create a Cloud Identity group and grant access to that group:
```bash
# First, create a group in Google Workspace Admin Console
# Example: billing-users@innovationbox.cloud

export ACCESS_CONTROL_TYPE="group"
export ACCESS_CONTROL_VALUE="billing-users@innovationbox.cloud"
./web/deploy/05-security-hardening.sh
```

#### Option C: Individual Users (Most Restrictive)
Grant access to specific users:
```bash
export ACCESS_CONTROL_TYPE="users"
export ACCESS_CONTROL_VALUE="user1@innovationbox.cloud,user2@innovationbox.cloud"
./web/deploy/05-security-hardening.sh
```

**How it works:**
- Users authenticate with their Google account (via IAP)
- Cloud Run checks if the user's email matches the IAM policy
- If yes → access granted
- If no → access denied

### 2. Can backend services use the same Service Account with a custom role?

**Yes!** This is exactly what we've implemented:

#### Current Setup (Before):
- Multiple service accounts: `agent-engine-api-sa`, `agent-engine-ui-sa`
- Multiple standard roles: `roles/bigquery.dataViewer`, `roles/aiplatform.user`, `roles/datastore.user`, etc.
- Over-privileged permissions

#### New Setup (After):
- Single service account: `agent-engine-api-sa` (for backend)
- Custom role: `roles/gcpBillingAgentService` (project-level custom role)
- Minimal permissions: Only what's actually needed

**What the custom role includes:**
- BigQuery: Read-only access to datasets and tables, ability to create jobs
- Vertex AI: Query reasoning engines
- Firestore: Full CRUD for query history
- Logging: Write logs

**What it excludes:**
- No write access to BigQuery (already blocked in agent config)
- No admin permissions
- No unnecessary permissions

## Implementation Steps

### Step 1: Run Security Hardening Script

```bash
cd web/deploy

# For domain-level access (recommended)
export PROJECT_ID="your-project-id"
export ACCESS_CONTROL_TYPE="domain"
export ACCESS_CONTROL_VALUE="innovationbox.cloud"
./05-security-hardening.sh
```

### Step 2: Test Access

1. Try accessing the UI with a user from your domain
2. Try with a user NOT from your domain (should be denied)
3. Check Cloud Run logs for any issues

### Step 3: Verify IAM Setup

```bash
# Check custom role
gcloud iam roles describe gcpBillingAgentService --project=PROJECT_ID

# Check service account permissions
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:agent-engine-api-sa@PROJECT_ID.iam.gserviceaccount.com"

# Check Cloud Run access
gcloud run services get-iam-policy agent-engine-ui \
  --region=us-central1 \
  --project=PROJECT_ID
```

## Security Benefits

### ✅ Access Control
- **Before**: Anyone with a Google account (`allAuthenticatedUsers`)
- **After**: Only users in your domain/group

### ✅ Principle of Least Privilege
- **Before**: Multiple standard roles with broad permissions
- **After**: Single custom role with minimal required permissions

### ✅ Auditability
- All access is logged
- Can see exactly who accessed what
- Can track permission changes

### ✅ Maintainability
- Single role to manage
- Clear permission boundaries
- Easy to review and update

## Migration Path

### Phase 1: Test (Recommended First)
```bash
# Keep allAuthenticatedUsers for now, but add custom role
export ACCESS_CONTROL_TYPE="allAuthenticatedUsers"
./05-security-hardening.sh
```

### Phase 2: Gradual Rollout
```bash
# Add domain access alongside allAuthenticatedUsers
# (Manually add both bindings)
```

### Phase 3: Full Migration
```bash
# Remove allAuthenticatedUsers, use only domain/group
export ACCESS_CONTROL_TYPE="domain"
export ACCESS_CONTROL_VALUE="innovationbox.cloud"
./05-security-hardening.sh
```

## Rollback Plan

If you need to rollback:
```bash
export ACCESS_CONTROL_TYPE="allAuthenticatedUsers"
./05-security-hardening.sh
```

Or manually:
```bash
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=us-central1 \
  --member="allAuthenticatedUsers" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

## Additional Security Ideas (Future)

### Secret Manager
Move sensitive configs to Secret Manager:
```bash
# Store REASONING_ENGINE_ID in Secret Manager
echo -n "your-reasoning-engine-id" | \
  gcloud secrets create reasoning-engine-id \
  --data-file=- \
  --project=PROJECT_ID

# Update Cloud Run to use secret
gcloud run services update agent-engine-api \
  --update-secrets=BQ_AGENT_MICK_REASONING_ENGINE_ID=reasoning-engine-id:latest \
  --region=us-central1 \
  --project=PROJECT_ID
```

### Cloud Armor
Enable DDoS protection and rate limiting:
```bash
# Create Cloud Armor policy
gcloud compute security-policies create billing-agent-policy \
  --description="Rate limiting for billing agent" \
  --project=PROJECT_ID

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy=billing-agent-policy \
  --expression="true" \
  --action="rate-based-ban" \
  --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600 \
  --project=PROJECT_ID
```

### VPC Connector
Use private networking for service-to-service communication:
```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create billing-agent-connector \
  --region=us-central1 \
  --subnet-project=PROJECT_ID \
  --subnet=default \
  --min-instances=2 \
  --max-instances=3 \
  --project=PROJECT_ID

# Update Cloud Run to use VPC connector
gcloud run services update agent-engine-api \
  --vpc-connector=billing-agent-connector \
  --region=us-central1 \
  --project=PROJECT_ID
```

## Summary

✅ **Use Cloud Identity for user access** - Domain, group, or individual user restrictions
✅ **Use single service account with custom role** - Minimal permissions, easy to manage
✅ **Follow principle of least privilege** - Only grant what's needed
✅ **Gradual migration path** - Test before full rollout

The scripts and configuration files are ready to use!

