# Security Improvements for GCP Billing Agent

## Current Security State

### Issues Identified:
1. **Open Access**: Using `allAuthenticatedUsers` - anyone with a Google account can access
2. **Scattered Permissions**: Multiple service accounts with different roles spread across multiple bindings
3. **Over-privileged Service Accounts**: Using standard roles that may grant more permissions than needed
4. **No Access Control**: No restriction by domain, organization, or group

## Proposed Security Improvements

### 1. Cloud Identity-Based Access Control ⭐ Recommended

**Replace `allAuthenticatedUsers` or `allUsers` with specific Cloud Identity controls:**

#### Option A: Organization-Level Restriction (Recommended for enterprise)
- Restrict to users in your organization/domain
- Example: `domain:innovationbox.cloud`
- **Benefits**: No OAuth consent screen needed, works immediately, fully automated
- **Implementation**: Use `make security-harden` with `ACCESS_CONTROL_TYPE=domain`

#### Option B: Group-Based Access
- Create Cloud Identity groups
- Grant access to specific groups
- Example: `group:billing-agents@innovationbox.cloud`
- **Benefits**: Fine-grained control, no OAuth consent screen needed
- **Implementation**: Use `make security-harden` with `ACCESS_CONTROL_TYPE=group`

#### Option C: Individual User Access
- Grant access to specific users
- Example: `user:john@innovationbox.cloud`
- **Benefits**: Most granular control
- **Implementation**: Use `make security-harden` with `ACCESS_CONTROL_TYPE=users`

### 2. Custom IAM Role with Least Privilege

**Create a custom role with only required permissions:**

Instead of multiple standard roles, create a single custom role:
- `roles/gcp-billing-agent-service` - Custom role with minimal permissions

**Required Permissions:**
- BigQuery: `bigquery.datasets.get`, `bigquery.jobs.create`, `bigquery.tables.getData`
- Vertex AI: `aiplatform.reasoningEngines.query`
- Firestore: `datastore.entities.create`, `datastore.entities.get`, `datastore.entities.list`, `datastore.entities.delete`
- Logging: `logging.logEntries.create`

### 3. Service Account Consolidation

**Use a single service account for backend services:**
- Single service account: `agent-engine-sa@PROJECT_ID.iam.gserviceaccount.com`
- Applies to: Cloud Run API, Agent Engine calls, Firestore access
- Single custom role binding

### 4. Additional Security Layers

#### A. Cloud Armor (DDoS Protection)
- Enable Cloud Armor for Cloud Run
- Rate limiting and DDoS protection

#### B. VPC Connector (Private Networking)
- Use VPC connector for private service-to-service communication
- Reduce exposure surface

#### C. Secret Management
- Move sensitive configs (REASONING_ENGINE_ID) to Secret Manager
- No hardcoded secrets in environment variables

#### D. Audit Logging
- Enable Cloud Audit Logs
- Monitor access patterns

#### E. Input Validation
- Backend validation of user inputs
- SQL injection prevention (already handled by BigQuery)
- XSS prevention in frontend

## Implementation Plan

### Phase 1: Access Control (Quick Win)
1. Replace `allAuthenticatedUsers` with domain/group restrictions
2. Update deployment scripts
3. Test with restricted users

### Phase 2: Custom IAM Role (Medium Effort)
1. Define custom IAM role YAML
2. Create role in GCP
3. Update service account bindings
4. Remove old role bindings
5. Test functionality

### Phase 3: Service Account Consolidation (Medium Effort)
1. Create unified service account
2. Update Cloud Run services
3. Update IAM bindings
4. Test end-to-end

### Phase 4: Advanced Security (Long Term)
1. Implement Secret Manager
2. Enable Cloud Armor
3. Set up VPC connector
4. Enable audit logging
5. Add monitoring/alerts

## Access Control Examples

### Organization Domain Restriction
```bash
# Allow only users from your organization
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=us-central1 \
  --member="domain:innovationbox.cloud" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

### Group-Based Access
```bash
# Create group first: billing-users@innovationbox.cloud
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=us-central1 \
  --member="group:billing-users@innovationbox.cloud" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

### Individual User Access
```bash
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=us-central1 \
  --member="user:john@innovationbox.cloud" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

## Custom IAM Role Definition

See `web/deploy/custom-iam-role.yaml` for the complete role definition.

## Migration Strategy

1. **Parallel Deployment**: Deploy new security config alongside existing
2. **Gradual Migration**: Move users to new access control
3. **Test Thoroughly**: Ensure all functionality works
4. **Remove Old Access**: Remove `allAuthenticatedUsers` after verification
5. **Monitor**: Watch for access issues

## Rollback Plan

If issues arise:
1. Re-add `allAuthenticatedUsers` temporarily
2. Investigate access issues
3. Fix and re-apply restrictions

