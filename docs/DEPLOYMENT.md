# Deployment Guide - ChatGCP

## Can I Deploy Frontend to Agent Engine?

**❌ No** - Vertex AI Agent Engine is specifically designed for deploying **AI agents** (Python backend logic), not web frontends.

**What Agent Engine is for:**
- Deploying ADK agents (your Python agent code)
- Hosting the agent's inference logic
- Providing REST API endpoints for querying agents

**What Agent Engine is NOT for:**
- Hosting React/Vue/Angular frontends
- Serving static HTML/CSS/JS files
- Web application hosting

## Deployment Options

### Option 1: Cloud Run (Recommended) ✅

**Best for:** Production deployments with full control

**Architecture:**
```
┌─────────────────────┐
│  React Frontend     │  Cloud Run (Static files + nginx)
│  (Port 8080)        │
└──────────┬──────────┘
           │ HTTP/HTTPS
           │
┌──────────▼──────────┐
│  FastAPI Backend    │  Cloud Run (Python API)
│  (Port 8080)        │
└──────────┬──────────┘
           │ REST API
           │
┌──────────▼──────────┐
│  Vertex AI          │
│  Agent Engine       │
└─────────────────────┘
```

**Pros:**
- ✅ Serverless (pay per use)
- ✅ Auto-scaling
- ✅ HTTPS by default
- ✅ IAM authentication
- ✅ Easy CI/CD
- ✅ Both frontend and backend can use Cloud Run

**Cons:**
- ⚠️ Cold starts (minimal for static files)
- ⚠️ Need to configure CORS properly

### Option 2: Cloud Storage + Cloud CDN (Frontend Only)

**Best for:** Static frontend with API backend elsewhere

**Architecture:**
```
┌─────────────────────┐
│  React Frontend     │  Cloud Storage + Cloud CDN
│  (Static files)     │  (Global CDN)
└──────────┬──────────┘
           │ HTTPS
           │
┌──────────▼──────────┐
│  FastAPI Backend    │  Cloud Run
│  (API)              │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Agent Engine       │
└─────────────────────┘
```

**Pros:**
- ✅ Ultra-fast global CDN
- ✅ Very cheap (storage + bandwidth)
- ✅ Excellent caching
- ✅ No server management

**Cons:**
- ⚠️ Need to handle CORS for API calls
- ⚠️ Need separate deployment for backend

### Option 3: Cloud Run (Combined)

**Best for:** Simplicity - single service deployment

Deploy both frontend and backend in one Cloud Run service.

**Pros:**
- ✅ Single deployment
- ✅ No CORS issues
- ✅ Simple architecture

**Cons:**
- ⚠️ Frontend and backend scale together
- ⚠️ Slightly more complex Dockerfile

## Recommended Deployment: Cloud Run (Separate Services)

We'll deploy:
1. **Backend API** → Cloud Run (Python FastAPI)
2. **Frontend** → Cloud Run (Static files with nginx)

## Security Considerations

### Current State: ❌ NOT SECURE

The current implementation:
- ❌ No authentication
- ❌ Open CORS (anyone can call the API)
- ❌ No rate limiting
- ❌ No input validation
- ✅ HTTPS (provided by Cloud Run)

### Production Security Requirements

1. **Authentication**
   - API keys
   - OAuth 2.0 (Google Sign-In)
   - IAM authentication (Cloud Run)

2. **Authorization**
   - User roles/permissions
   - Per-agent access control

3. **Network Security**
   - Restricted CORS
   - VPC networking (optional)
   - Cloud Armor (DDoS protection)

4. **Data Security**
   - Input validation
   - Output sanitization
   - Rate limiting
   - Request logging

5. **Compliance**
   - Audit logging
   - Data encryption at rest
   - Data encryption in transit (HTTPS)

## Deployment Steps

### Option 1: IAP + Load Balancer (Recommended for Production) ✅

**Complete secure deployment with IAP authentication and load balancer:**

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
export DOMAIN="agent-engine.yourdomain.com"
./deploy-all.sh
```

This deploys:
- ✅ VPC + Load Balancer
- ✅ IAP Authentication
- ✅ SSL/TLS
- ✅ Secure networking

See [README.md](./README.md) for detailed instructions.

### Option 2: Simple Cloud Run (Development/Testing)

See separate guides:
- [Backend Deployment to Cloud Run](./DEPLOYMENT_BACKEND.md)
- [Frontend Deployment to Cloud Run](./DEPLOYMENT_FRONTEND.md)
- [Security Hardening](./SECURITY.md)

