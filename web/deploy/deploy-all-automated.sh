#!/bin/bash

# Fully Automated Deployment Script
# This script handles everything: infrastructure, IAM, security, deployment
# Designed for forking and use with innovationbox.cloud or any organization

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration with defaults
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
DOMAIN="${DOMAIN:-asl.apps-eval.com}"  # Default to asl.apps-eval.com
ACCESS_CONTROL_TYPE="${ACCESS_CONTROL_TYPE:-domain}"  # domain, group, users, or allAuthenticatedUsers
ACCESS_CONTROL_VALUE="${ACCESS_CONTROL_VALUE:-asl.apps-eval.com}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to check if resource exists (returns 0 if exists, 1 if not)
check_resource_exists() {
    local resource_type="$1"
    local resource_name="$2"
    
    case "$resource_type" in
        "service-account")
            gcloud iam service-accounts describe "$resource_name@$PROJECT_ID.iam.gserviceaccount.com" \
                --project="$PROJECT_ID" >/dev/null 2>&1
            ;;
        "firestore-db")
            gcloud firestore databases describe --project="$PROJECT_ID" >/dev/null 2>&1
            ;;
        "iam-role")
            gcloud iam roles describe "$resource_name" --project="$PROJECT_ID" >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}

# Check prerequisites
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ ERROR: PROJECT_ID must be set${NC}"
    echo "Usage: export PROJECT_ID=your-project-id && ./deploy-all-automated.sh"
    echo "Or: PROJECT_ID=your-project-id ./deploy-all-automated.sh"
    exit 1
fi

echo -e "${BLUE}🚀 Fully Automated Deployment${NC}"
echo -e "${BLUE}=============================${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Domain: $DOMAIN"
echo "  Access Control: $ACCESS_CONTROL_TYPE"
if [ -n "$ACCESS_CONTROL_VALUE" ]; then
    echo "  Access Control Value: $ACCESS_CONTROL_VALUE"
fi
echo ""

# Check for -y or --yes flag to skip confirmation
SKIP_CONFIRM=false
for arg in "$@"; do
    case $arg in
        -y|--yes)
            SKIP_CONFIRM=true
            shift
            ;;
        *)
            ;;
    esac
done

if [ "$SKIP_CONFIRM" = false ]; then
    read -p "Continue with fully automated deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deployment cancelled.${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${BLUE}Step 1: Enabling Required APIs...${NC}"
gcloud services enable \
    compute.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    storage.googleapis.com \
    firestore.googleapis.com \
    bigquery.googleapis.com \
    aiplatform.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    --project="$PROJECT_ID" \
    --quiet

echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

echo -e "${BLUE}Step 2: Creating Service Accounts...${NC}"
API_SERVICE_ACCOUNT="agent-engine-api-sa"
FRONTEND_SERVICE_ACCOUNT="agent-engine-ui-sa"

if check_resource_exists "service-account" "$API_SERVICE_ACCOUNT"; then
    echo -e "${YELLOW}  ⚠️  $API_SERVICE_ACCOUNT already exists${NC}"
else
    gcloud iam service-accounts create "$API_SERVICE_ACCOUNT" \
        --display-name='Agent Engine API Service Account' \
        --description='Service account for Agent Engine API backend' \
        --project="$PROJECT_ID" \
        --quiet
    echo -e "${GREEN}  ✅ $API_SERVICE_ACCOUNT created${NC}"
fi

if check_resource_exists "service-account" "$FRONTEND_SERVICE_ACCOUNT"; then
    echo -e "${YELLOW}  ⚠️  $FRONTEND_SERVICE_ACCOUNT already exists${NC}"
else
    gcloud iam service-accounts create "$FRONTEND_SERVICE_ACCOUNT" \
        --display-name='Agent Engine UI Service Account' \
        --description='Service account for Agent Engine frontend' \
        --project="$PROJECT_ID" \
        --quiet
    echo -e "${GREEN}  ✅ $FRONTEND_SERVICE_ACCOUNT created${NC}"
fi
echo ""

echo -e "${BLUE}Step 3: Creating Firestore Database...${NC}"
if check_resource_exists "firestore-db" "default"; then
    echo -e "${YELLOW}  ⚠️  Firestore database already exists${NC}"
else
    echo -e "${BLUE}  Creating Firestore database (this may take a few minutes)...${NC}"
    gcloud firestore databases create \
        --location="$REGION" \
        --type=firestore-native \
        --project="$PROJECT_ID" \
        --quiet || {
        echo -e "${YELLOW}  ⚠️  Firestore creation may have failed or already exists${NC}"
    }
    echo -e "${GREEN}  ✅ Firestore database ready${NC}"
fi
echo ""

echo -e "${BLUE}Step 4: Creating Custom IAM Role...${NC}"
CUSTOM_ROLE_ID="gcpBillingAgentService"
CUSTOM_ROLE_NAME="projects/$PROJECT_ID/roles/$CUSTOM_ROLE_ID"

if check_resource_exists "iam-role" "$CUSTOM_ROLE_ID"; then
    echo -e "${YELLOW}  ⚠️  Custom role already exists. Updating...${NC}"
    gcloud iam roles update "$CUSTOM_ROLE_ID" \
        --project="$PROJECT_ID" \
        --file="$SCRIPT_DIR/custom-iam-role.yaml" \
        --quiet
else
    echo -e "${BLUE}  Creating custom IAM role...${NC}"
    gcloud iam roles create "$CUSTOM_ROLE_ID" \
        --project="$PROJECT_ID" \
        --file="$SCRIPT_DIR/custom-iam-role.yaml" \
        --quiet
fi
echo -e "${GREEN}  ✅ Custom IAM role ready${NC}"
echo ""

echo -e "${BLUE}Step 5: Granting IAM Permissions...${NC}"

# Remove old role bindings (ignore errors if they don't exist)
echo -e "${BLUE}  Cleaning up old role bindings...${NC}"
for role in "roles/bigquery.dataViewer" "roles/bigquery.jobUser" "roles/aiplatform.user" "roles/datastore.user"; do
    gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$API_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="$role" \
        --quiet 2>/dev/null || true
done

# Grant custom role to API service account
echo -e "${BLUE}  Granting custom role to API service account...${NC}"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$API_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$CUSTOM_ROLE_NAME" \
    --quiet

# Grant logging role (required for Cloud Run)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$API_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter" \
    --quiet

# Grant Cloud Build permissions (for deployment)
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

echo -e "${BLUE}  Granting Cloud Build permissions...${NC}"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/run.admin" \
    --quiet

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/iam.serviceAccountUser" \
    --quiet

# Grant service account user permission for Cloud Build
gcloud iam service-accounts add-iam-policy-binding "$API_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/iam.serviceAccountUser" \
    --project="$PROJECT_ID" \
    --quiet

gcloud iam service-accounts add-iam-policy-binding "$FRONTEND_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/iam.serviceAccountUser" \
    --project="$PROJECT_ID" \
    --quiet

echo -e "${GREEN}  ✅ IAM permissions configured${NC}"
echo ""

echo -e "${BLUE}Step 6: Deploying Applications...${NC}"
export PROJECT_ID REGION
"$SCRIPT_DIR/03-applications-iap.sh"
echo ""

e

echo -e "${BLUE}Step 7: Creating Load Balancer...${NC}"
export PROJECT_ID REGION DOMAIN
"$SCRIPT_DIR/04-load-balancer.sh"
echo ""

echo -e "${BLUE}Step 8: Configuring Authentication...${NC}"
export PROJECT_ID REGION
"$SCRIPT_DIR/06-configure-authentication.sh" -y 2>/dev/null || echo -e "${YELLOW}⚠️  Some authentication setup may require manual steps${NC}"
echo ""

echo -e "${BLUE}Step 9: Applying Security Hardening...${NC}"
export PROJECT_ID REGION ACCESS_CONTROL_TYPE ACCESS_CONTROL_VALUE
"$SCRIPT_DIR/05-security-hardening.sh"
echo ""

echo -e "${GREEN}🎉 FULLY AUTOMATED DEPLOYMENT COMPLETE!${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "  ✅ All required APIs enabled"
echo "  ✅ Service accounts created"
echo "  ✅ Firestore database created"
echo "  ✅ Custom IAM role created and applied"
echo "  ✅ IAM permissions configured"
echo "  ✅ Cloud Run services deployed"
echo "  ✅ Authentication APIs enabled"
echo "  ⚠️  OAuth consent screen may need manual configuration (see docs/AUTHENTICATION_SETUP.md)"
echo "  ✅ Security hardening applied"
echo "  ✅ Access control configured ($ACCESS_CONTROL_TYPE: $ACCESS_CONTROL_VALUE)"
echo ""
echo -e "${BLUE}🌐 Service URLs:${NC}"
API_URL=$(gcloud run services describe agent-engine-api --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "Not deployed")
UI_URL=$(gcloud run services describe agent-engine-ui --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "Not deployed")
echo "  API: $API_URL"
echo "  UI: $UI_URL"
echo ""
echo -e "${YELLOW}⚠️  Next Steps:${NC}"
echo "  1. Deploy your agents to Vertex AI Agent Engine"
echo "  2. Update REASONING_ENGINE_ID in bq_agent_mick/.env"
echo "  3. Redeploy if needed: ./03-applications-iap.sh"
echo "  4. Test access with users from your domain"
echo ""
echo -e "${GREEN}🚀 Everything is automated and ready!${NC}"

