# Deployment FAQ - Your Questions Answered

## 1. Can I Deploy the Frontend to Agent Engine?

**❌ No, you cannot deploy the frontend to Agent Engine.**

### Why Not?

**Agent Engine is specifically for:**
- Deploying AI agents (Python backend logic)
- Hosting agent inference code
- Providing REST API endpoints for querying agents

**Agent Engine is NOT for:**
- Hosting React/Vue/Angular frontends
- Serving static HTML/CSS/JS files
- Web application hosting

### What Agent Engine Does

When you deploy an agent with `adk deploy agent_engine`, it:
1. Packages your Python agent code
2. Creates a Reasoning Engine instance
3. Exposes REST API endpoints (`/query`, `/streamQuery`)
4. Handles agent execution and inference

It's a **backend service**, not a web server.

---

## 2. Should We Deploy to Cloud Run?

**✅ Yes, Cloud Run is the recommended option!**

### Recommended Architecture

```
┌─────────────────────────┐
│  React Frontend         │  → Cloud Run (nginx + static files)
│  (Port 8080)            │     or Cloud Storage + CDN
└──────────┬──────────────┘
           │ HTTPS
           │
┌──────────▼──────────────┐
│  FastAPI Backend        │  → Cloud Run (Python API)
│  (Port 8080)            │
└──────────┬──────────────┘
           │ REST API
           │
┌──────────▼──────────────┐
│  Vertex AI              │  → Already deployed via ADK
│  Agent Engine           │     (Your agents are here)
└─────────────────────────┘
```

### Why Cloud Run?

**Pros:**
- ✅ **Serverless** - Pay only for what you use
- ✅ **Auto-scaling** - Scales to zero when not in use
- ✅ **HTTPS by default** - Automatic SSL certificates
- ✅ **Easy deployment** - Simple `gcloud run deploy` command
- ✅ **IAM authentication** - Built-in Google Cloud authentication
- ✅ **Global deployment** - Deploy to multiple regions
- ✅ **Cost-effective** - Free tier available, then pay-per-use

**Cons:**
- ⚠️ **Cold starts** - First request may be slower (minimal for static files)
- ⚠️ **CORS configuration** - Need to configure CORS properly

### Deployment Options

#### Option 1: Cloud Run (Separate Services) ✅ Recommended

**Frontend:**
- Deploy React build to Cloud Run with nginx
- Serves static files
- Fast, scalable

**Backend:**
- Deploy FastAPI to Cloud Run
- Handles API requests
- Can scale independently

**Pros:**
- Frontend and backend scale independently
- Can update one without affecting the other
- Better resource allocation

#### Option 2: Cloud Storage + CDN (Frontend Only)

**Frontend:**
- Deploy to Cloud Storage
- Serve via Cloud CDN
- Ultra-fast global distribution

**Backend:**
- Deploy to Cloud Run (as above)

**Pros:**
- Very cheap for static files
- Global CDN (faster loading)
- Excellent caching

**Cons:**
- Need to handle CORS for API calls
- Separate deployment processes

#### Option 3: Combined Cloud Run Service

**Both frontend and backend in one service:**
- nginx serves frontend
- nginx proxies API calls to FastAPI
- Single deployment

**Pros:**
- Single deployment
- No CORS issues

**Cons:**
- Frontend and backend scale together
- Less flexible

**👉 Recommendation: Use Option 1 (Separate Cloud Run services)**

See [DEPLOYMENT_BACKEND.md](./DEPLOYMENT_BACKEND.md) and [DEPLOYMENT_FRONTEND.md](./DEPLOYMENT_FRONTEND.md) for step-by-step instructions.

---

## 3. Will the Frontend Be Secure?

**✅ YES - With IAP + Load Balancer Deployment!**

We've created deployment scripts that mirror your provisioner project setup, including **IAP (Identity-Aware Proxy)** and **load balancer** for production-grade security.

### Deployment Options

#### Option A: Simple IAP (No DNS Required!) ✅ **RECOMMENDED**

**Fully secure with Cloud Run's native IAP:**
- ✅ **IAP Authentication** - Users authenticate with Google accounts
- ✅ **No DNS Required** - Uses Cloud Run's default URLs
- ✅ **No Load Balancer** - Simpler and cheaper
- ✅ **HTTPS by Default** - Cloud Run provides SSL
- ✅ **Easy Deployment** - Single script

**Deploy with:**
```bash
cd web/deploy
export PROJECT_ID="your-project-id"
./deploy-simple-iap.sh
```

See [README-SIMPLE.md](./README-SIMPLE.md) for full instructions.

#### Option B: IAP + Load Balancer (Custom Domain)

**For custom domains and path-based routing:**
- ✅ **IAP Authentication** - Users authenticate with Google accounts
- ✅ **Load Balancer** - Global HTTPS endpoint
- ✅ **Custom Domain** - Use your own domain
- ✅ **Path Routing** - `/api/*` → backend
- ⚠️ **DNS Required** - Need to configure DNS

**Deploy with:**
```bash
cd web/deploy
export PROJECT_ID="your-project-id"
export DOMAIN="agent-engine.yourdomain.com"
./deploy-all.sh
```

See [README.md](./README.md) for full instructions.

#### Option C: Simple Cloud Run (Development/Testing)

**⚠️ Current State: NOT SECURE**

The basic Cloud Run deployment has **no authentication** and is **not production-ready**.

### Current Security Issues

- ❌ **No authentication** - Anyone can call the API
- ❌ **Open CORS** - Any website can make requests
- ❌ **No rate limiting** - Vulnerable to abuse
- ❌ **No input validation** - Potential injection attacks
- ✅ **HTTPS** - Automatic with Cloud Run (this is good!)

### What You Need for Production

#### 1. Authentication

**Option A: IAM Authentication (Recommended)**
- Use Google Cloud IAM
- Users authenticate with Google accounts
- Automatic token validation
- Integrated with Cloud Run

**Option B: API Key Authentication**
- Simple API key in headers
- Good for service-to-service calls
- Less secure for user-facing apps

#### 2. CORS Restrictions

```python
# Only allow your frontend domain
allow_origins=[
    "https://your-frontend-domain.com",
    "http://localhost:3000",  # Dev only
]
```

#### 3. Rate Limiting

```python
# Limit requests per IP
@limiter.limit("10/minute")
```

#### 4. Input Validation

```python
# Validate and sanitize inputs
message: constr(min_length=1, max_length=10000)
```

#### 5. Security Headers

```nginx
# In nginx.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

### Security Checklist

Before deploying to production:

- [ ] Add authentication (IAM or API key)
- [ ] Restrict CORS to your frontend domain
- [ ] Add rate limiting
- [ ] Validate all inputs
- [ ] Configure security headers
- [ ] Use Secret Manager for sensitive data
- [ ] Enable Cloud Run authentication
- [ ] Set up monitoring and alerting
- [ ] Regular security audits

### Full Security Guide

See [SECURITY.md](./SECURITY.md) for:
- Step-by-step authentication setup
- Code examples for all security measures
- Cloud Run security configuration
- Testing and monitoring

---

## Summary

| Question | Answer |
|----------|--------|
| **Can frontend go to Agent Engine?** | ❌ No - Agent Engine is for AI agents only |
| **Should we use Cloud Run?** | ✅ Yes - Recommended for both frontend and backend |
| **Is it secure?** | ✅ Yes - With IAP + Load Balancer deployment (see deploy/README.md) |

## IAP + Load Balancer Deployment

**✅ YES - We've created deployment scripts with IAP support!**

Just like your provisioner project, we now have:
- ✅ IAP (Identity-Aware Proxy) authentication
- ✅ Load balancer with SSL/TLS
- ✅ VPC networking
- ✅ Secure backend services

**Quick Start:**
```bash
cd web/deploy
export PROJECT_ID="your-project-id"
export DOMAIN="agent-engine.yourdomain.com"
./deploy-all.sh
```

## Next Steps

1. **For Development:**
   - Use local deployment (current setup)
   - Good for testing and development

2. **For Production:**
   - Deploy backend to Cloud Run (see [DEPLOYMENT_BACKEND.md](./DEPLOYMENT_BACKEND.md))
   - Deploy frontend to Cloud Run (see [DEPLOYMENT_FRONTEND.md](./DEPLOYMENT_FRONTEND.md))
   - Implement security measures (see [SECURITY.md](./SECURITY.md))

3. **Quick Start:**
   ```bash
   # Backend
   cd web/backend
   gcloud run deploy agent-engine-api --source .
   
   # Frontend
   cd web/frontend
   npm run build
   gcloud run deploy agent-engine-ui --source .
   ```

---

**Questions?** See the full documentation:
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment overview
- [DEPLOYMENT_BACKEND.md](./DEPLOYMENT_BACKEND.md) - Backend deployment
- [DEPLOYMENT_FRONTEND.md](./DEPLOYMENT_FRONTEND.md) - Frontend deployment
- [SECURITY.md](./SECURITY.md) - Security hardening

