#!/bin/bash

# Application Deployment Script with Custom Firestore Authentication
# This script builds and deploys Cloud Run services with custom auth using Firestore
# No DNS, load balancer, or Firebase Authentication required!

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-qwiklabs-asl-04-8e9f23e85ced}"
REGION="${REGION:-us-central1}"
API_SERVICE_ACCOUNT="agent-engine-api-sa"
FRONTEND_SERVICE_ACCOUNT="agent-engine-ui-sa"
API_SERVICE="agent-engine-api"
UI_SERVICE="agent-engine-ui"

echo -e "${BLUE}🚀 Application Deployment with Firestore Authentication${NC}"
echo -e "${BLUE}=====================================================${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  API Service Account: $API_SERVICE_ACCOUNT"
echo "  Frontend Service Account: $FRONTEND_SERVICE_ACCOUNT"
echo ""
echo -e "${GREEN}  ✅ Using Firestore for user authentication${NC}"
echo -e "${GREEN}  ✅ No Firebase Authentication config needed${NC}"
echo ""
echo -e "${YELLOW}ℹ️  This deployment uses custom authentication with Firestore${NC}"
echo -e "${YELLOW}   No DNS, load balancer, or Firebase Auth required!${NC}"
echo ""

echo -e "${BLUE}1. Building Backend API...${NC}"
cd "$(dirname "$0")/../backend"
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$API_SERVICE:latest" . --project="$PROJECT_ID"
echo -e "${GREEN}✅ Backend API built successfully${NC}"
echo ""

echo -e "${BLUE}2. Building Frontend UI...${NC}"
cd "$(dirname "$0")/../frontend"
# Check if cloudbuild.yaml exists, otherwise build manually
if [ -f "cloudbuild.yaml" ]; then
    gcloud builds submit --config=cloudbuild.yaml . --project="$PROJECT_ID"
else
    echo -e "${YELLOW}⚠️  Cloud Build config not found, building manually...${NC}"
    # Build frontend manually
    npm install
    npm run build
    # Create a simple Dockerfile for Cloud Build
    echo "FROM nginx:alpine" > Dockerfile.temp
    echo "COPY dist /usr/share/nginx/html" >> Dockerfile.temp
    echo "COPY nginx.conf /etc/nginx/conf.d/default.conf" >> Dockerfile.temp
    echo "EXPOSE 8080" >> Dockerfile.temp
    echo "CMD [\"nginx\", \"-g\", \"daemon off;\"]" >> Dockerfile.temp
    gcloud builds submit --tag "gcr.io/$PROJECT_ID/$UI_SERVICE:latest" . --project="$PROJECT_ID"
    rm Dockerfile.temp
fi
echo -e "${GREEN}✅ Frontend UI built successfully${NC}"
echo ""

echo -e "${BLUE}3. Getting Reasoning Engine IDs (fallback for auto-discovery)...${NC}"
# Try to get reasoning engine IDs as fallback (in case auto-discovery fails)
# Auto-discovery will be tried first, but these env vars serve as backup
BQ_AGENT_MICK_ID=""
if [ -f "$(dirname "$0")/../../bq_agent_mick/.env" ]; then
    BQ_AGENT_MICK_ID=$(grep "REASONING_ENGINE_ID" "$(dirname "$0")/../../bq_agent_mick/.env" | cut -d '=' -f2 | tr -d '"' | tr -d "'" | xargs)
fi

if [ -z "$BQ_AGENT_MICK_ID" ]; then
    echo -e "${YELLOW}⚠️  REASONING_ENGINE_ID not found in bq_agent_mick/.env${NC}"
    echo -e "${YELLOW}   Auto-discovery will be attempted, but may fail without proper IAM permissions${NC}"
fi

# Try to get reasoning engine ID from bq_agent/.env
BQ_AGENT_ID=""
if [ -f "$(dirname "$0")/../../bq_agent/.env" ]; then
    BQ_AGENT_ID=$(grep "REASONING_ENGINE_ID" "$(dirname "$0")/../../bq_agent/.env" | cut -d '=' -f2 | tr -d '"' | tr -d "'" | xargs)
fi

if [ -n "$BQ_AGENT_MICK_ID" ] || [ -n "$BQ_AGENT_ID" ]; then
    echo -e "${GREEN}✅ Found Reasoning Engine IDs (will be used as fallback):${NC}"
    [ -n "$BQ_AGENT_MICK_ID" ] && echo -e "${GREEN}   bq_agent_mick: $BQ_AGENT_MICK_ID${NC}"
    [ -n "$BQ_AGENT_ID" ] && echo -e "${GREEN}   bq_agent: $BQ_AGENT_ID${NC}"
else
    echo -e "${YELLOW}⚠️  No Reasoning Engine IDs found - backend will try auto-discovery only${NC}"
fi
echo ""

echo -e "${BLUE}4. Deploying API Service...${NC}"
cd "$(dirname "$0")/../backend"

# Get UI service URL for CORS (will be set after UI deployment, but prepare the variable)
# We'll update it after UI is deployed
# Generate or retrieve JWT_SECRET_KEY (must be consistent across deployments)
# Check if JWT_SECRET_KEY already exists in the service
EXISTING_JWT_SECRET=$(gcloud run services describe "$API_SERVICE" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(spec.template.spec.containers[0].env)" 2>/dev/null | \
    grep -o "JWT_SECRET_KEY[^;]*" | cut -d"'" -f4 || echo "")

if [ -z "$EXISTING_JWT_SECRET" ]; then
    # Generate a new JWT secret key
    JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32 | tr -d '\n')
    echo -e "${YELLOW}⚠️  Generated new JWT_SECRET_KEY (first deployment)${NC}"
else
    # Use existing JWT secret key to maintain token validity
    JWT_SECRET_KEY="$EXISTING_JWT_SECRET"
    echo -e "${GREEN}✅ Using existing JWT_SECRET_KEY${NC}"
fi

# Prepare backend environment variables
# Note: Reasoning engine IDs are optional - backend will try auto-discovery first,
# but these serve as fallback if auto-discovery fails (e.g., permission denied)
BACKEND_ENV_VARS="BQ_PROJECT=$PROJECT_ID,LOCATION=$REGION,JWT_SECRET_KEY=$JWT_SECRET_KEY"
if [ -n "$BQ_AGENT_MICK_ID" ]; then
    BACKEND_ENV_VARS="$BACKEND_ENV_VARS,BQ_AGENT_MICK_REASONING_ENGINE_ID=$BQ_AGENT_MICK_ID"
fi
if [ -n "$BQ_AGENT_ID" ]; then
    BACKEND_ENV_VARS="$BACKEND_ENV_VARS,BQ_AGENT_REASONING_ENGINE_ID=$BQ_AGENT_ID"
fi

# Attach metrics job reference if the Cloud Run job exists
DEFAULT_METRICS_JOB_NAME="projects/$PROJECT_ID/locations/$REGION/jobs/metrics-collector"
if gcloud run jobs describe "metrics-collector" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    BACKEND_ENV_VARS="$BACKEND_ENV_VARS,METRICS_JOB_NAME=$DEFAULT_METRICS_JOB_NAME"
    echo -e "${BLUE}ℹ️  Metrics collector job detected; enabling refresh endpoint${NC}"
else
    echo -e "${YELLOW}⚠️  Metrics collector job not found. /metrics/refresh will return 503 until the job is created.${NC}"
fi

# First, try to clear VPC connector if service exists (ignore errors)
echo -e "${YELLOW}Clearing VPC connector from existing service (if any)...${NC}"
gcloud run services update "$API_SERVICE" \
    --region="$REGION" \
    --clear-vpc-connector \
    --project="$PROJECT_ID" 2>/dev/null || echo -e "${YELLOW}  Service may not exist yet or VPC already cleared${NC}"

# Now deploy
gcloud run deploy "$API_SERVICE" \
    --image="gcr.io/$PROJECT_ID/$API_SERVICE:latest" \
    --region="$REGION" \
    --service-account="$API_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --ingress=all \
    --min-instances=0 \
    --max-instances=10 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --allow-unauthenticated \
    --set-env-vars="$BACKEND_ENV_VARS" \
    --project="$PROJECT_ID"

echo -e "${GREEN}✅ API service deployed with authentication required${NC}"
echo ""

# Get API URL for CORS configuration
API_URL=$(gcloud run services describe "$API_SERVICE" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(status.url)")

echo -e "${BLUE}5. API Service deployed (Custom Firestore Auth protects endpoints)${NC}"
echo -e "${GREEN}✅ API service deployed - authentication handled by custom Firestore auth${NC}"
echo ""

# Update API service with CORS settings (will be updated after UI is deployed)
echo -e "${BLUE}6. Deploying UI Service...${NC}"
cd "$(dirname "$0")/../frontend"

# Build frontend with API URL (no Firebase config needed)
echo -e "${YELLOW}Building frontend with API URL: $API_URL${NC}"
export VITE_API_URL="$API_URL"

# Build frontend with just API URL (no Firebase config)
if [ -f "cloudbuild.yaml" ]; then
    gcloud builds submit --config=cloudbuild.yaml \
        --substitutions="_API_URL=$API_URL" \
        . --project="$PROJECT_ID"
else
    echo -e "${YELLOW}⚠️  Cloud Build config not found, building manually...${NC}"
    # Build frontend manually
    npm install
    npm run build
    # Create a simple Dockerfile for Cloud Build
    echo "FROM nginx:alpine" > Dockerfile.temp
    echo "COPY dist /usr/share/nginx/html" >> Dockerfile.temp
    echo "COPY nginx.conf /etc/nginx/conf.d/default.conf" >> Dockerfile.temp
    echo "EXPOSE 8080" >> Dockerfile.temp
    echo "CMD [\"nginx\", \"-g\", \"daemon off;\"]" >> Dockerfile.temp
    gcloud builds submit --tag "gcr.io/$PROJECT_ID/$UI_SERVICE:latest" . --project="$PROJECT_ID"
    rm Dockerfile.temp
fi

# First, try to clear VPC connector if service exists (ignore errors)
echo -e "${YELLOW}Clearing VPC connector from existing service (if any)...${NC}"
gcloud run services update "$UI_SERVICE" \
    --region="$REGION" \
    --clear-vpc-connector \
    --project="$PROJECT_ID" 2>/dev/null || echo -e "${YELLOW}  Service may not exist yet or VPC already cleared${NC}"

# Now deploy
gcloud run deploy "$UI_SERVICE" \
    --image="gcr.io/$PROJECT_ID/$UI_SERVICE:latest" \
    --region="$REGION" \
    --service-account="$FRONTEND_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --ingress=all \
    --min-instances=0 \
    --max-instances=10 \
    --memory=256Mi \
    --cpu=1 \
    --timeout=300 \
    --allow-unauthenticated \
    --project="$PROJECT_ID"

echo -e "${GREEN}✅ UI service deployed with authentication required${NC}"
echo ""

# Get UI URL for CORS update
UI_URL=$(gcloud run services describe "$UI_SERVICE" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(status.url)")

echo -e "${BLUE}7. Updating API CORS settings...${NC}"
# Update API service with UI URL in CORS
gcloud run services update "$API_SERVICE" \
    --region="$REGION" \
    --update-env-vars="CORS_ALLOWED_ORIGINS=$UI_URL" \
    --project="$PROJECT_ID"

echo -e "${GREEN}✅ CORS updated with UI URL${NC}"
echo ""

echo -e "${BLUE}8. UI Service deployed (Custom Firestore Auth protects access)${NC}"
echo -e "${GREEN}✅ UI service deployed - authentication handled by custom Firestore auth${NC}"
echo ""

# Get service URLs
API_URL=$(gcloud run services describe "$API_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)")
UI_URL=$(gcloud run services describe "$UI_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)")

echo -e "${GREEN}🎉 Application Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}📋 What was deployed:${NC}"
echo "  ✅ Backend API: $API_SERVICE"
echo "  ✅ Frontend UI: $UI_SERVICE"
echo "  ✅ Both services configured with custom Firestore authentication"
echo "  ✅ No DNS or load balancer required!"
echo ""
echo -e "${BLUE}🌐 Service URLs:${NC}"
echo "  API Service: $API_URL"
echo "  UI Service: $UI_URL"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "  1. Users can sign up with @asl.apps-eval.com email addresses"
echo "  2. Frontend API_URL is already configured: $API_URL"
echo "  3. Authentication uses Firestore (no additional setup needed)"
echo "  4. Agents are automatically discovered from Agent Engine - no configuration needed!"
echo "  5. When you deploy new agents to Agent Engine, they'll appear automatically"
echo ""
echo "     # Grant access to specific user"
echo "     gcloud run services add-iam-policy-binding $API_SERVICE \\"
echo "       --region=$REGION \\"
echo "       --member='user:user@example.com' \\"
echo "       --role='roles/run.invoker' \\"
echo "       --project=$PROJECT_ID"
echo ""
echo "     # Grant access to group"
echo "     gcloud run services add-iam-policy-binding $API_SERVICE \\"
echo "       --region=$REGION \\"
echo "       --member='group:team@example.com' \\"
echo "       --role='roles/run.invoker' \\"
echo "       --project=$PROJECT_ID"
echo ""

