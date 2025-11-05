# Simple IAP Deployment - No DNS Required!

This is a **simplified deployment** that uses **Cloud Run's native IAP support** instead of a load balancer. Perfect if you don't have a domain or want to avoid DNS setup!

## Key Differences

| Feature | Load Balancer Setup | Simple IAP Setup |
|---------|-------------------|------------------|
| **DNS Required** | ❌ Yes | ✅ No |
| **Load Balancer** | ❌ Yes | ✅ No |
| **SSL Certificate** | ❌ Yes | ✅ No (handled by Cloud Run) |
| **Complexity** | High | Low |
| **IAP Support** | ✅ Yes | ✅ Yes |
| **Cost** | Higher | Lower |
| **Custom Domain** | ✅ Yes | ❌ No (uses .run.app URLs) |

## Quick Start

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
export REGION="us-central1"
./deploy-simple-iap.sh
```

That's it! No DNS, no load balancer, just secure Cloud Run services with IAP.

## What Gets Created

1. ✅ **Infrastructure** (VPC, Service Accounts) - optional, can skip if you don't need VPC
2. ✅ **IAM Permissions** - required for service accounts
3. ✅ **Cloud Run Services** - Backend and Frontend
4. ✅ **IAP Authentication** - Users authenticate with Google accounts

## How It Works

```
User
 ↓
Cloud Run Service (with IAP)
 ↓
Google Authentication
 ↓
If authenticated → Access granted
If not → Redirect to Google login
```

## Access Your Services

After deployment, you'll get URLs like:
- **API**: `https://agent-engine-api-xxxxx-uc.a.run.app`
- **UI**: `https://agent-engine-ui-xxxxx-uc.a.run.app`

Users accessing these URLs will:
1. Be redirected to Google login (if not authenticated)
2. After login, access the service
3. All requests are authenticated via IAP

## Granting Access

### All Authenticated Users (Default)

By default, all authenticated Google users can access. This is set by:
```bash
gcloud run services add-iam-policy-binding agent-engine-api \
  --region=us-central1 \
  --member="allAuthenticatedUsers" \
  --role="roles/run.invoker" \
  --project=YOUR_PROJECT_ID
```

### Specific Users

```bash
gcloud run services add-iam-policy-binding agent-engine-api \
  --region=us-central1 \
  --member="user:user@example.com" \
  --role="roles/run.invoker" \
  --project=YOUR_PROJECT_ID
```

### Specific Groups

```bash
gcloud run services add-iam-policy-binding agent-engine-api \
  --region=us-central1 \
  --member="group:team@example.com" \
  --role="roles/run.invoker" \
  --project=YOUR_PROJECT_ID
```

### Remove Public Access

```bash
gcloud run services remove-iam-policy-binding agent-engine-api \
  --region=us-central1 \
  --member="allAuthenticatedUsers" \
  --role="roles/run.invoker" \
  --project=YOUR_PROJECT_ID
```

## Configuration

### Update Frontend API URL

After deployment, update the frontend to use the API URL:

```bash
# Get the API URL
API_URL=$(gcloud run services describe agent-engine-api \
  --region=us-central1 \
  --project=YOUR_PROJECT_ID \
  --format="value(status.url)")

# Update frontend .env or rebuild with API_URL
```

Or set it as an environment variable in Cloud Run:
```bash
gcloud run services update agent-engine-ui \
  --region=us-central1 \
  --update-env-vars="VITE_API_URL=$API_URL" \
  --project=YOUR_PROJECT_ID
```

## Advantages

✅ **No DNS setup** - Use Cloud Run's default URLs  
✅ **No load balancer** - Simpler architecture  
✅ **Lower cost** - No load balancer fees  
✅ **HTTPS by default** - Cloud Run provides SSL  
✅ **IAP authentication** - Secure with Google accounts  
✅ **Easy deployment** - Single script  

## Disadvantages

⚠️ **No custom domain** - Uses `.run.app` URLs  
⚠️ **Separate URLs** - API and UI have different URLs  
⚠️ **No path-based routing** - Can't route `/api/*` to backend  

## When to Use

**Use Simple IAP if:**
- ✅ You don't have a domain
- ✅ You want quick deployment
- ✅ You don't need custom domains
- ✅ You want lower costs
- ✅ Separate API/UI URLs are fine

**Use Load Balancer if:**
- ✅ You need a custom domain
- ✅ You want path-based routing (`/api/*`)
- ✅ You need enterprise features
- ✅ You have a domain ready

## Troubleshooting

### Can't Access Services

1. **Check IAM policy:**
   ```bash
   gcloud run services get-iam-policy agent-engine-api \
     --region=us-central1 \
     --project=YOUR_PROJECT_ID
   ```

2. **Verify authentication:**
   - Make sure you're logged in: `gcloud auth login`
   - Try accessing the URL in an incognito window

3. **Check service status:**
   ```bash
   gcloud run services describe agent-engine-api \
     --region=us-central1 \
     --project=YOUR_PROJECT_ID
   ```

### API Calls Failing

1. **Check CORS** - Make sure backend allows frontend origin
2. **Check API URL** - Verify frontend is using correct API URL
3. **Check authentication** - API calls need to include auth token

## Cleanup (For Course/Temporary Deployments)

When you're done with your course, clean up all resources:

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
./cleanup.sh
```

See [QUICK_START.md](./QUICK_START.md) for quick reference.

This will delete:
- ✅ Cloud Run services
- ✅ Service accounts  
- ✅ VPC infrastructure
- ✅ Load balancer resources (if any)

**Note:** Container images are kept (they're cheap and useful for re-deployment).

## Migration to Load Balancer

If you later want to use a load balancer:

1. Run the full deployment scripts (`deploy-all.sh`)
2. Update DNS
3. Grant IAP access on backend services
4. Update frontend API URL

Your Cloud Run services will work with both setups!

## Comparison with Provisioner Project

The provisioner project uses a load balancer because it needs:
- Custom domain (`api.innovationbox.cloud`)
- Path-based routing (`/api/*` → backend)
- Enterprise features

For this agent engine chat, **Simple IAP is often sufficient** and much easier to set up!

