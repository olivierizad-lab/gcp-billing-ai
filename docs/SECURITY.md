# Security Guide - ChatGCP

## Current Security Status

### ❌ NOT PRODUCTION READY

The current implementation has **no authentication** and is **not secure** for production use.

**Current Issues:**
- ❌ No authentication required
- ❌ Open CORS (anyone can call the API)
- ❌ No rate limiting
- ❌ No input validation
- ❌ No API key protection
- ✅ HTTPS (provided by Cloud Run)

## Security Requirements for Production

### 1. Authentication & Authorization

#### Option A: IAM Authentication (Recommended for GCP)

**Backend:**
```python
# In web/backend/main.py
from fastapi import FastAPI, Depends, HTTPException, Header
from google.auth.transport import requests
from google.auth import jwt
import os

async def verify_iam_token(authorization: str = Header(None)):
    """Verify Google IAM token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        token = authorization.replace("Bearer ", "")
        # Verify token with Google
        request = requests.Request()
        decoded_token = jwt.verify_firebase_token(token, request)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

@app.post("/query/stream")
async def query_stream(request: QueryRequest, user: dict = Depends(verify_iam_token)):
    # User is authenticated
    return StreamingResponse(...)
```

**Frontend:**
```javascript
// Get ID token from Google Sign-In
async function getAuthToken() {
  const auth = await gapi.auth2.getAuthInstance();
  const user = auth.currentUser.get();
  const token = user.getAuthResponse().id_token;
  return token;
}

// Use in API calls
const token = await getAuthToken();
fetch(`${API_URL}/query/stream`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

#### Option B: API Key Authentication

**Backend:**
```python
# In web/backend/main.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
import os

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    valid_key = os.getenv("API_KEY")
    if not valid_key or api_key != valid_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.post("/query/stream")
async def query_stream(request: QueryRequest, api_key: str = Depends(verify_api_key)):
    return StreamingResponse(...)
```

**Set API key:**
```bash
gcloud run services update agent-engine-api \
  --region us-central1 \
  --update-env-vars API_KEY=your-secret-key-here
```

**Frontend:**
```javascript
fetch(`${API_URL}/query/stream`, {
  headers: {
    'X-API-Key': 'your-api-key'  // In production, use environment variable
  }
});
```

### 2. CORS Configuration

**Restrict CORS to specific domains:**

```python
# In web/backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com",  # Production frontend
        "http://localhost:3000",  # Local dev only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    max_age=3600,
)
```

### 3. Rate Limiting

**Add rate limiting middleware:**

```python
# Install: pip install slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/query/stream")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def query_stream(request: Request, ...):
    ...
```

### 4. Input Validation

**Validate and sanitize inputs:**

```python
from pydantic import BaseModel, validator, constr

class QueryRequest(BaseModel):
    message: constr(min_length=1, max_length=10000)  # Max 10KB
    agent_name: constr(regex="^[a-z_]+$")  # Only lowercase letters and underscores
    user_id: Optional[str] = None
    
    @validator('message')
    def validate_message(cls, v):
        # Check for SQL injection attempts
        dangerous_patterns = ['DROP', 'DELETE', 'TRUNCATE', ';--']
        if any(pattern in v.upper() for pattern in dangerous_patterns):
            raise ValueError('Potentially dangerous input detected')
        return v.strip()
```

### 5. Error Handling

**Don't expose sensitive information:**

```python
# Bad
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # Exposes internal errors

# Good
except Exception as e:
    logger.error(f"Internal error: {str(e)}")  # Log internally
    raise HTTPException(status_code=500, detail="An internal error occurred")  # Generic message
```

### 6. Request Logging & Monitoring

```python
import logging
from fastapi import Request
import time

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.2f}s - "
        f"IP: {request.client.host}"
    )
    return response
```

### 7. Cloud Run Security Settings

```bash
# Deploy with authentication required
gcloud run deploy agent-engine-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0

# Set up Cloud Armor for DDoS protection
# https://cloud.google.com/armor/docs/configure-security-policies
```

### 8. Environment Variable Security

**Use Secret Manager for sensitive data:**

```bash
# Create secret
echo -n "your-api-key" | gcloud secrets create api-key --data-file=-

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding api-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Use in Cloud Run
gcloud run services update agent-engine-api \
  --region us-central1 \
  --update-secrets API_KEY=api-key:latest
```

**In code:**
```python
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')

API_KEY = get_secret("api-key")
```

## Security Checklist

Before deploying to production:

- [ ] Authentication implemented (IAM or API key)
- [ ] CORS restricted to specific domains
- [ ] Rate limiting enabled
- [ ] Input validation in place
- [ ] Error messages don't expose sensitive info
- [ ] Request logging configured
- [ ] Cloud Run authentication enabled
- [ ] Secrets stored in Secret Manager
- [ ] HTTPS enforced (automatic with Cloud Run)
- [ ] Security headers configured (nginx for frontend)
- [ ] Regular security audits scheduled
- [ ] Monitoring and alerting set up

## Testing Security

```bash
# Test authentication
curl -X POST https://your-api-url/query \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' 
# Should return 401

# Test with valid token
curl -X POST https://your-api-url/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
# Should work

# Test rate limiting
for i in {1..15}; do
  curl -X POST https://your-api-url/query \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}'
done
# Should start returning 429 after limit
```

## Additional Resources

- [Cloud Run Security Best Practices](https://cloud.google.com/run/docs/securing)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

