# Authentication Setup for Cloud Run

## Overview

Cloud Run services can use several authentication methods. **For Google Workspace/Cloud Identity organizations, domain-based restrictions are the recommended approach** as they work immediately without requiring OAuth consent screen configuration.

## Recommended Solution: Domain/Group Restrictions ⭐

**This is the recommended approach for organizations with Google Workspace or Cloud Identity:**

### Why Domain Restrictions?

1. ✅ **Works immediately** - No OAuth consent screen configuration needed
2. ✅ **More secure** - Restrict access to your organization/domain
3. ✅ **Fully automated** - Can be scripted and deployed automatically
4. ✅ **No manual steps** - No Console configuration required
5. ✅ **Better for production** - Enterprise-grade access control

### Implementation

```bash
# Use the security hardening script with domain restrictions
make security-harden \
  PROJECT_ID=your-project \
  ACCESS_CONTROL_TYPE=domain \
  ACCESS_CONTROL_VALUE=innovationbox.cloud
```

Or manually:
```bash
# Domain restriction
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=us-central1 \
  --member="domain:innovationbox.cloud" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID

gcloud run services add-iam-policy-binding agent-engine-api \
  --region=us-central1 \
  --member="domain:innovationbox.cloud" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

**What this does:**
- Only users with `@innovationbox.cloud` email addresses can access
- Users are automatically redirected to Google sign-in
- No OAuth consent screen configuration needed
- Works with Google Workspace/Cloud Identity

## Alternative Solutions

### Option 1: Manual OAuth Consent Screen Configuration (For External Users)

**Steps:**
1. Go to: https://console.cloud.google.com/apis/credentials/consent?project=YOUR_PROJECT_ID
2. Configure OAuth consent screen:
   - **User Type**: 
     - Internal (if using Google Workspace/Cloud Identity)
     - External (if allowing any Google account)
   - **App name**: GCP Billing Agent
   - **Support email**: your-email@domain.com
   - **Authorized domains**: your-domain.com (e.g., `asl.apps-eval.com`)
3. Add scopes (if needed):
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
4. Save and continue

**After configuration:**
- Cloud Run services with `allAuthenticatedUsers` should redirect to Google sign-in
- Users authenticate with Google accounts
- Access is granted based on IAM policy

### Option 2: Use `allUsers` (Less Secure, But Works)

For testing, you can use `allUsers` which makes services publicly accessible:
```bash
gcloud run services add-iam-policy-binding SERVICE_NAME \
  --region=REGION \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

**Pros:**
- Works immediately
- No authentication required
- Good for testing

**Cons:**
- **NOT SECURE** - anyone on internet can access
- Not suitable for production

### Option 3: Group-Based Restrictions

For fine-grained control, use Cloud Identity groups:

```bash
# Create group first (in Google Admin Console or Cloud Identity)
# Then grant access:
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=REGION \
  --member="group:billing-users@innovationbox.cloud" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

**Pros:**
- Fine-grained control (specific groups)
- No OAuth consent screen needed
- Works with Google Workspace/Cloud Identity
- Can combine multiple groups

**Cons:**
- Requires Google Workspace/Cloud Identity groups
- Groups must be created first

## Automated Setup Script

We have a script that enables APIs and provides instructions:
```bash
make configure-auth PROJECT_ID=your-project
# or
cd web/deploy
./06-configure-authentication.sh
```

This script:
- ✅ Enables required APIs (IAP)
- ✅ Provides instructions for domain restrictions (recommended)
- ⚠️  Provides manual steps for OAuth consent screen (if needed)

## Recommendation by Use Case

### For Google Workspace/Cloud Identity Organizations (Recommended)
**Use domain restrictions** - No OAuth consent screen needed:
```bash
make security-harden \
  PROJECT_ID=your-project \
  ACCESS_CONTROL_TYPE=domain \
  ACCESS_CONTROL_VALUE=your-domain.com
```

### For External Users (Any Google Account)
**Use OAuth consent screen** - Requires manual configuration:
1. Configure OAuth consent screen in Console
2. Use `allAuthenticatedUsers` IAM policy
3. Users authenticate with any Google account

### For Testing (Temporary)
**Use `allUsers`** - Public access, works immediately:
```bash
gcloud run services add-iam-policy-binding agent-engine-ui \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --region=REGION \
  --project=PROJECT_ID
```
⚠️ **NOT SECURE** - Use only for testing!

## Automation Limitations

**Cannot be automated:**
- OAuth consent screen configuration (requires Console)
- Setting user type (Internal/External)
- Adding authorized domains
- Configuring scopes

**Can be automated:**
- Enabling APIs
- Setting IAM policies
- Deploying services
- Configuring service accounts

## Troubleshooting

### 403 Forbidden with Domain Restrictions

**Check:**
1. You're logged in with the correct domain email
2. IAM policy has `domain:your-domain.com`
3. Wait 60 seconds for IAM propagation
4. Clear browser cache/cookies
5. Try incognito window
6. Verify your email domain matches exactly

**Verify domain:**
```bash
gcloud run services get-iam-policy agent-engine-ui \
  --region=REGION \
  --project=PROJECT_ID
```

### 403 Forbidden with `allAuthenticatedUsers`

**Check:**
1. OAuth consent screen is configured (if using external users)
2. IAM policy has `allAuthenticatedUsers`
3. Wait 60 seconds for IAM propagation
4. Clear browser cache/cookies
5. Try incognito window

**Solution:**
- If using Google Workspace/Cloud Identity: **Switch to domain restrictions instead**
- If using external users: Configure OAuth consent screen manually

### No Redirect to Google Sign-In

**Possible causes:**
1. OAuth consent screen not configured (for external users)
2. Browser sending invalid auth headers
3. IAM policy not propagated
4. Project-level OAuth configuration issue

**Solution:**
- **Recommended**: Use domain/group restrictions (works without OAuth consent screen)
- **Alternative**: Configure OAuth consent screen manually (for external users)

## References

- [Cloud Run Authentication](https://cloud.google.com/run/docs/authenticating)
- [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)
- [IAM for Cloud Run](https://cloud.google.com/run/docs/securing/managing-access)

