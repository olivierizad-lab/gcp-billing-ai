# Simple IAP Deployment - No DNS Required!

Perfect solution if you don't have a domain or want to avoid DNS setup complexity.

## Quick Start

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
export REGION="us-central1"
./deploy-simple-iap.sh
```

**That's it!** No DNS, no load balancer, just secure Cloud Run services with IAP.

## How It Works

Cloud Run has **native IAP support** built-in. When you deploy a service with `--no-allow-unauthenticated`, users must authenticate with Google accounts to access it.

```
User → Cloud Run Service → Google Authentication → Access Granted
```

## What You Get

- ✅ **Secure** - IAP authentication required
- ✅ **HTTPS** - Automatic SSL/TLS
- ✅ **No DNS** - Uses Cloud Run URLs (`.run.app`)
- ✅ **No Load Balancer** - Simpler and cheaper
- ✅ **Easy** - Single script deployment

## Service URLs

After deployment, you'll get URLs like:
- **API**: `https://agent-engine-api-xxxxx-uc.a.run.app`
- **UI**: `https://agent-engine-ui-xxxxx-uc.a.run.app`

Users accessing these URLs will:
1. Be redirected to Google login (if not authenticated)
2. After login, access the service
3. All requests are authenticated via IAP

## Granting Access

### Default: All Authenticated Users

By default, all authenticated Google users can access. To restrict:

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

After deployment, update the frontend to use the API URL:

```bash
# Get the API URL
API_URL=$(gcloud run services describe agent-engine-api \
  --region=us-central1 \
  --project=YOUR_PROJECT_ID \
  --format="value(status.url)")

echo "Update frontend API_URL to: $API_URL"
```

Or set it as an environment variable in Cloud Run:
```bash
gcloud run services update agent-engine-ui \
  --region=us-central1 \
  --update-env-vars="VITE_API_URL=$API_URL" \
  --project=YOUR_PROJECT_ID
```

## Comparison

| Feature | Simple IAP | Load Balancer |
|---------|-----------|---------------|
| **DNS Required** | ❌ No | ✅ Yes |
| **Load Balancer** | ❌ No | ✅ Yes |
| **Custom Domain** | ❌ No | ✅ Yes |
| **Path Routing** | ❌ No | ✅ Yes |
| **Cost** | Lower | Higher |
| **Complexity** | Low | High |
| **IAP** | ✅ Yes | ✅ Yes |

## When to Use

**Use Simple IAP if:**
- ✅ You don't have a domain
- ✅ You want quick deployment
- ✅ Separate API/UI URLs are fine
- ✅ You want lower costs

**Use Load Balancer if:**
- ✅ You need a custom domain
- ✅ You want path-based routing (`/api/*`)
- ✅ You have a domain ready

## See Also

- [README-SIMPLE.md](./README-SIMPLE.md) - Detailed documentation
- [README.md](./README.md) - Load balancer deployment guide

