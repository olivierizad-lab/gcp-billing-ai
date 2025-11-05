# Frontend Deployment to Cloud Run

Deploy the React frontend to Google Cloud Run as static files with nginx.

## Prerequisites

```bash
# Install gcloud CLI
# Set your project
gcloud config set project YOUR_PROJECT_ID
```

## Step 1: Build the Frontend

```bash
cd web/frontend

# Install dependencies
npm install

# Build for production
npm run build
```

This creates a `dist/` folder with optimized static files.

## Step 2: Create Dockerfile with nginx

Create `web/frontend/Dockerfile`:

```dockerfile
# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

## Step 3: Create nginx Configuration

Create `web/frontend/nginx.conf`:

```nginx
server {
    listen 8080;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Serve static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API proxy (optional - if you want to proxy API calls through frontend)
    # Uncomment if you want to avoid CORS issues
    # location /api {
    #     proxy_pass https://YOUR-BACKEND-URL;
    #     proxy_set_header Host $host;
    #     proxy_set_header X-Real-IP $remote_addr;
    #     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #     proxy_set_header X-Forwarded-Proto $scheme;
    # }
}
```

## Step 4: Configure API URL

Create `web/frontend/.env.production`:

```bash
VITE_API_URL=https://agent-engine-api-xxxxx-uc.a.run.app
```

Or update `vite.config.js` to use environment variable:

```javascript
export default defineConfig({
  plugins: [react()],
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(
      process.env.VITE_API_URL || 'https://agent-engine-api-xxxxx-uc.a.run.app'
    ),
  },
})
```

## Step 5: Update .dockerignore

Create `web/frontend/.dockerignore`:

```
node_modules
dist
.git
.env.local
.env.development
.env.production
npm-debug.log
```

## Step 6: Deploy to Cloud Run

```bash
cd web/frontend

# Deploy (unauthenticated for public access)
gcloud run deploy agent-engine-ui \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080

# Or deploy with authentication
gcloud run deploy agent-engine-ui \
  --source . \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --port 8080
```

## Step 7: Get Service URL

After deployment:

```bash
# Get the URL
gcloud run services describe agent-engine-ui \
  --region us-central1 \
  --format 'value(status.url)'
```

You'll get a URL like:
```
https://agent-engine-ui-xxxxx-uc.a.run.app
```

## Step 8: Update Backend CORS

Update `web/backend/main.py` to allow your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agent-engine-ui-xxxxx-uc.a.run.app",  # Your frontend URL
        "http://localhost:3000",  # Local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then redeploy the backend.

## Step 9: Test the Deployment

Open your frontend URL in a browser:
```
https://agent-engine-ui-xxxxx-uc.a.run.app
```

You should see the ChatGCP interface!

## Alternative: Deploy to Cloud Storage + Cloud CDN

For even better performance and lower cost:

```bash
# Build the frontend
cd web/frontend
npm run build

# Create a bucket
gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://agent-engine-ui

# Upload files
gsutil -m cp -r dist/* gs://agent-engine-ui/

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://agent-engine-ui

# Enable static website hosting
gsutil web set -m index.html -e index.html gs://agent-engine-ui

# Set up Cloud CDN (optional)
# https://cloud.google.com/cdn/docs/setting-up-cdn-with-buckets
```

Then access via:
```
https://storage.googleapis.com/agent-engine-ui/index.html
```

Or set up a custom domain with Cloud CDN.

## Troubleshooting

### 404 errors on page refresh

This is normal for SPAs. The nginx config handles this with `try_files $uri $uri/ /index.html;`.

### CORS errors

Make sure your backend CORS configuration includes your frontend domain.

### API calls failing

Check that `VITE_API_URL` is set correctly in your build environment.

### Build fails

Make sure all dependencies are in `package.json`:
```bash
npm install
npm run build
```

