# Troubleshooting 403 Forbidden on Cloud Run

## Issue
Getting 403 Forbidden when accessing Cloud Run service with `allAuthenticatedUsers` IAM policy.

## Root Cause
Cloud Run services with `--no-allow-unauthenticated` require authentication. When `allAuthenticatedUsers` is in the IAM policy, Cloud Run should redirect unauthenticated browser requests to Google sign-in. However, if the browser is sending invalid/stale auth headers, Cloud Run returns 403 instead of redirecting.

## Debugging Steps

### 1. Check IAM Policy
```bash
gcloud run services get-iam-policy SERVICE_NAME \
  --region=REGION \
  --project=PROJECT_ID
```

Verify `allAuthenticatedUsers` is present.

### 2. Check Audit Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME AND httpRequest.status=403" \
  --limit=10 \
  --project=PROJECT_ID \
  --format="json"
```

Look for the error message: "The request was not authenticated"

### 3. Test with Authenticated Request
```bash
# This should work
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://SERVICE_URL
```

If this works, the IAM policy is correct and the issue is browser authentication.

### 4. Browser Debugging
1. Open Developer Tools (F12)
2. Go to Network tab
3. Clear network log
4. Access the URL
5. Check request/response headers
6. Look for:
   - `Authorization` header (should not be present or invalid)
   - `Location` header in response (should redirect to Google sign-in)
   - Status code (should be 302 redirect, not 403)

### 5. Clear Browser Data
1. Clear all cookies for `*.run.app` and `*.google.com`
2. Clear browser cache
3. Close all browser windows
4. Open fresh browser window
5. Access the URL

## Solutions

### Solution 1: Wait for IAM Propagation
IAM policy changes can take up to 60 seconds to propagate:
```bash
# Wait 60 seconds after changing IAM policy
sleep 60
# Then test access
```

### Solution 2: Force IAM Policy Refresh
Remove and re-add the IAM binding:
```bash
gcloud run services remove-iam-policy-binding SERVICE_NAME \
  --region=REGION \
  --member="allAuthenticatedUsers" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID

sleep 5

gcloud run services add-iam-policy-binding SERVICE_NAME \
  --region=REGION \
  --member="allAuthenticatedUsers" \
  --role="roles/run.invoker" \
  --project=PROJECT_ID
```

### Solution 3: Check Browser Authentication
Ensure you're accessing from a browser that:
- Has no cached authentication
- Is not sending invalid auth headers
- Can properly handle OAuth redirects

### Solution 4: Verify Service Configuration
Ensure the service was deployed correctly:
```bash
gcloud run services describe SERVICE_NAME \
  --region=REGION \
  --project=PROJECT_ID \
  --format="get(spec.template.spec.serviceAccountName)"
```

## Expected Behavior

With `allAuthenticatedUsers` in IAM policy:
- **Unauthenticated browser request**: Should redirect (302) to Google sign-in
- **Authenticated browser request**: Should return 200 OK
- **Unauthenticated curl request**: Returns 403 (expected, no browser OAuth flow)
- **Authenticated curl request**: Returns 200 OK

## If Still Not Working

1. Check if IAM API is enabled:
   ```bash
   gcloud services list --enabled --filter="name:iam.googleapis.com"
   ```

2. Verify project-level IAM permissions

3. Check Cloud Run service logs for more details:
   ```bash
   gcloud run services logs read SERVICE_NAME \
     --region=REGION \
     --project=PROJECT_ID \
     --limit=50
   ```

4. Consider temporarily allowing unauthenticated access for testing:
   ```bash
   # NOT RECOMMENDED FOR PRODUCTION
   gcloud run services add-iam-policy-binding SERVICE_NAME \
     --region=REGION \
     --member="allUsers" \
     --role="roles/run.invoker" \
     --project=PROJECT_ID
   ```

