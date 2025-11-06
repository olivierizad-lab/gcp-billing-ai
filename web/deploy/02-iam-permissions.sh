#!/bin/bash

# IAM Permissions Setup Script (Part 2 of 4)
# This script sets up all the IAM permissions for the service accounts
# Based on provisioner project deployment pattern

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-qwiklabs-asl-04-8e9f23e85ced}"
API_SERVICE_ACCOUNT="agent-engine-api-sa"
FRONTEND_SERVICE_ACCOUNT="agent-engine-ui-sa"

# Get the Cloud Build service account (dynamic)
CLOUD_BUILD_SERVICE_ACCOUNT=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")-compute@developer.gserviceaccount.com

echo -e "${BLUE}🔐 IAM Permissions Setup (Part 2/4)${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  API Service Account: $API_SERVICE_ACCOUNT"
echo "  Frontend Service Account: $FRONTEND_SERVICE_ACCOUNT"
echo "  Cloud Build Service Account: $CLOUD_BUILD_SERVICE_ACCOUNT"
echo ""

echo -e "${BLUE}1. Creating Custom IAM Role (if needed)...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CUSTOM_ROLE_ID="gcpBillingAgentService"
CUSTOM_ROLE_NAME="projects/$PROJECT_ID/roles/$CUSTOM_ROLE_ID"

if gcloud iam roles describe "$CUSTOM_ROLE_ID" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Custom role already exists. Updating...${NC}"
    gcloud iam roles update "$CUSTOM_ROLE_ID" \
        --project="$PROJECT_ID" \
        --file="$SCRIPT_DIR/custom-iam-role.yaml" \
        --quiet
else
    echo -e "${BLUE}Creating custom IAM role...${NC}"
    gcloud iam roles create "$CUSTOM_ROLE_ID" \
        --project="$PROJECT_ID" \
        --file="$SCRIPT_DIR/custom-iam-role.yaml" \
        --quiet
fi
echo -e "${GREEN}✅ Custom IAM role ready${NC}"
echo ""

echo -e "${BLUE}2. Granting API Service Account - Project Level Permissions...${NC}"

# Remove old role bindings (ignore errors if they don't exist)
for role in "roles/bigquery.dataViewer" "roles/bigquery.jobUser" "roles/aiplatform.user" "roles/datastore.user"; do
    gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$API_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="$role" \
        --quiet 2>/dev/null || true
done

# Grant custom role to API service account
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$API_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$CUSTOM_ROLE_NAME" \
    --quiet

# Grant logging role (required for Cloud Run)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$API_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter" \
    --quiet

echo -e "${GREEN}✅ Project-level permissions granted${NC}"
echo ""

echo -e "${BLUE}3. Granting Frontend Service Account Permissions...${NC}"

# Frontend service account permissions
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$FRONTEND_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --quiet

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$FRONTEND_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser" \
    --quiet

echo -e "${GREEN}✅ Frontend service account permissions granted${NC}"
echo ""

echo -e "${BLUE}4. Granting Cloud Build Service Account Permissions...${NC}"

# Cloud Build service account permissions (for build logs and deployment)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$CLOUD_BUILD_SERVICE_ACCOUNT" \
    --role="roles/logging.logWriter" \
    --quiet

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$CLOUD_BUILD_SERVICE_ACCOUNT" \
    --role="roles/storage.admin" \
    --quiet

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$CLOUD_BUILD_SERVICE_ACCOUNT" \
    --role="roles/run.developer" \
    --quiet

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$CLOUD_BUILD_SERVICE_ACCOUNT" \
    --role="roles/iam.serviceAccountUser" \
    --quiet

echo -e "${GREEN}✅ Cloud Build service account permissions granted${NC}"
echo ""

echo -e "${GREEN}🎉 IAM Permissions Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📋 What was configured:${NC}"
echo "  ✅ API Service Account permissions (BigQuery, Vertex AI, Logging)"
echo "  ✅ Frontend Service Account permissions"
echo "  ✅ Cloud Build Service Account permissions"
echo ""
echo -e "${BLUE}🔄 Next steps:${NC}"
echo "  1. Run: ./web/deploy/03-applications.sh"
echo "  2. Run: ./web/deploy/04-load-balancer.sh"
echo ""

