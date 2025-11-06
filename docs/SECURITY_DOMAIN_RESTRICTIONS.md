# Cloud Run Domain Restrictions - Troubleshooting

## Issue: 403 Forbidden After Domain Restriction

When applying domain restrictions to Cloud Run services, you may encounter 403 errors even if the user's email matches the domain.

## Why This Happens

Cloud Run IAP (Identity-Aware Proxy) domain restrictions require:

1. **Proper Authentication**: The user must be authenticated via Google in the browser, not just via `gcloud` CLI
2. **IAM Policy Propagation**: IAM changes can take up to 60 seconds to propagate
3. **Google Workspace/Cloud Identity**: Domain restrictions work best with managed domains in Google Workspace or Cloud Identity

## Solutions

### Option 1: Use `allAuthenticatedUsers` (Less Secure, But Works)

For testing and development:
```bash
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=us-central1 \
  --member="allAuthenticatedUsers" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

**Pros:**
- Works immediately
- No authentication issues
- Good for testing

**Cons:**
- Any Google account can access
- Less secure for production

### Option 2: Domain Restriction (More Secure, But Requires Setup)

For production:
```bash
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=us-central1 \
  --member="domain:asl.apps-eval.com" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

**Requirements:**
- Domain must be managed in Google Workspace or Cloud Identity
- Users must authenticate via Google in browser (not just CLI)
- Users must be part of the domain organization

**Troubleshooting:**
1. Clear browser cache and cookies
2. Sign out and sign back in with domain account
3. Wait 1-2 minutes for IAM propagation
4. Check user's email matches domain exactly

### Option 3: Group-Based Access (Most Flexible)

Create a Cloud Identity group and grant access:
```bash
# Create group (in Google Workspace Admin Console)
# Then grant access:
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=us-central1 \
  --member="group:billing-users@asl.apps-eval.com" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

**Pros:**
- More granular control
- Can add/remove users from group
- Works with domain restrictions

**Cons:**
- Requires Google Workspace/Cloud Identity
- Requires group management

### Option 4: Individual User Access (Most Restrictive)

Grant access to specific users:
```bash
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=us-central1 \
  --member="user:user1@asl.apps-eval.com" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

## Current Recommendation for asl.apps-eval.com

For now, use **`allAuthenticatedUsers`** with domain restrictions as a backup:

```bash
# Both policies together
gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=us-central1 \
  --member="allAuthenticatedUsers" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID

gcloud run services add-iam-policy-binding agent-engine-ui \
  --region=us-central1 \
  --member="domain:asl.apps-eval.com" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

This ensures:
- Anyone with a Google account can access (for testing)
- Domain restriction is in place for future enforcement
- Easy to remove `allAuthenticatedUsers` when ready

## Testing Domain Restrictions

1. **Sign out of all Google accounts** in your browser
2. **Sign in with a user from the domain** (e.g., `user@asl.apps-eval.com`)
3. **Wait 1-2 minutes** for IAM propagation
4. **Try accessing the service**
5. **Check browser console** for authentication errors

## For Production (innovationbox.cloud)

When ready for production:
1. Remove `allAuthenticatedUsers` completely
2. Use domain restriction: `domain:innovationbox.cloud`
3. Or use group-based access for more control
4. Test thoroughly with multiple users
5. Monitor Cloud Run logs for access issues

## Additional Security

Consider:
- Cloud Armor for additional protection
- Rate limiting
- IP restrictions (if needed)
- Audit logging

