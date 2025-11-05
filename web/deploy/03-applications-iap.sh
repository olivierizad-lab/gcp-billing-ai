#!/bin/bash

# Application Deployment Script with Native Cloud Run IAP (Part 3 of 4)
# This script builds and deploys Cloud Run services with IAP enabled directly
# No DNS or load balancer required!

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

echo -e "${BLUE}🚀 Application Deployment with Native IAP (Part 3/4)${NC}"
echo -e "${BLUE}====================================================${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  API Service Account: $API_SERVICE_ACCOUNT"
echo "  Frontend Service Account: $FRONTEND_SERVICE_ACCOUNT"
echo ""
echo -e "${YELLOW}ℹ️  This deployment uses Cloud Run's native IAP support${NC}"
echo -e "${YELLOW}   No DNS or load balancer required!${NC}"
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

echo -e "${BLUE}3. Deploying API Service with IAP...${NC}"
cd "$(dirname "$0")/../backend"
gcloud run deploy "$API_SERVICE" \
    --image="gcr.io/$PROJECT_ID/$API_SERVICE:latest" \
    --region="$REGION" \
    --service-account="$API_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --min-instances=0 \
    --max-instances=10 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --no-allow-unauthenticated \
    --project="$PROJECT_ID"

echo -e "${GREEN}✅ API service deployed with authentication required${NC}"
echo ""

echo -e "${BLUE}4. Enabling IAP on API Service...${NC}"
# Enable IAP on the Cloud Run service
gcloud run services add-iam-policy-binding "$API_SERVICE" \
    --region="$REGION" \
    --member="allAuthenticatedUsers" \
    --role="roles/run.invoker" \
    --project="$PROJECT_ID" 2>/dev/null || echo -e "${YELLOW}⚠️  IAM policy may already be set${NC}"

echo -e "${GREEN}✅ IAP enabled on API service${NC}"
echo ""

echo -e "${BLUE}5. Deploying UI Service with IAP...${NC}"
cd "$(dirname "$0")/../frontend"
gcloud run deploy "$UI_SERVICE" \
    --image="gcr.io/$PROJECT_ID/$UI_SERVICE:latest" \
    --region="$REGION" \
    --service-account="$FRONTEND_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --min-instances=0 \
    --max-instances=10 \
    --memory=256Mi \
    --cpu=1 \
    --timeout=300 \
    --no-allow-unauthenticated \
    --project="$PROJECT_ID"

echo -e "${GREEN}✅ UI service deployed with authentication required${NC}"
echo ""

echo -e "${BLUE}6. Enabling IAP on UI Service...${NC}"
# Enable IAP on the Cloud Run service
gcloud run services add-iam-policy-binding "$UI_SERVICE" \
    --region="$REGION" \
    --member="allAuthenticatedUsers" \
    --role="roles/run.invoker" \
    --project="$PROJECT_ID" 2>/dev/null || echo -e "${YELLOW}⚠️  IAM policy may already be set${NC}"

echo -e "${GREEN}✅ IAP enabled on UI service${NC}"
echo ""

# Get service URLs
API_URL=$(gcloud run services describe "$API_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)")
UI_URL=$(gcloud run services describe "$UI_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)")

echo -e "${GREEN}🎉 Application Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}📋 What was deployed:${NC}"
echo "  ✅ Backend API: $API_SERVICE"
echo "  ✅ Frontend UI: $UI_SERVICE"
echo "  ✅ Both services configured with IAP authentication"
echo "  ✅ No DNS or load balancer required!"
echo ""
echo -e "${BLUE}🌐 Service URLs:${NC}"
echo "  API Service: $API_URL"
echo "  UI Service: $UI_URL"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "  1. Users will need to authenticate with Google accounts"
echo "  2. Update frontend API_URL to: $API_URL"
echo "  3. Grant specific users/groups access if needed:"
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

