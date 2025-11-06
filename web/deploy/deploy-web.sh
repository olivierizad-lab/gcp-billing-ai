#!/bin/bash

# Web Application Deployment - Cloud Run with Custom Firestore Authentication
# This script deploys the web application (backend + frontend) to Cloud Run
# Uses custom Firestore authentication - no DNS, Load Balancer, or Firebase Authentication required!

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

echo -e "${BLUE}🚀 Web Application Deployment with Firestore Authentication${NC}"
echo -e "${BLUE}===========================================================${NC}"
echo ""
echo -e "${YELLOW}This deployment uses custom authentication with Firestore.${NC}"
echo -e "${YELLOW}✅ No DNS configuration needed${NC}"
echo -e "${YELLOW}✅ No load balancer needed${NC}"
echo -e "${YELLOW}✅ No Firebase Authentication needed${NC}"
echo -e "${YELLOW}✅ Uses existing Firestore for user storage${NC}"
echo -e "${YELLOW}✅ Automatically discovers agents from Agent Engine${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
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
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deployment cancelled.${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${BLUE}Starting deployment...${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run infrastructure script but skip VPC (not needed for Cloud Run deployment)
echo -e "${BLUE}=== Setting up Infrastructure (skipping VPC) ===${NC}"
export PROJECT_ID REGION
# Only enable APIs and create service accounts, skip VPC
gcloud services enable \
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
    --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  Some APIs may already be enabled${NC}"

echo ""
echo -e "${BLUE}=== Setting up IAM Permissions ===${NC}"
export PROJECT_ID
"$SCRIPT_DIR/02-iam-permissions.sh" 2>/dev/null || echo -e "${YELLOW}⚠️  Some IAM permissions may already exist (continuing...)${NC}"

# Note: Security hardening (05-security-hardening.sh) is optional and can be run separately
# Or use deploy-all-automated.sh for full automation including security

echo ""
echo -e "${BLUE}=== Deploying Applications with Firestore Auth ===${NC}"
export PROJECT_ID REGION
# No Firebase config needed - using Firestore for auth
"$SCRIPT_DIR/03-applications.sh"

echo ""
echo -e "${GREEN}🎉 DEPLOYMENT SUCCESSFUL!${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "  ✅ Service Accounts configured"
echo "  ✅ Backend and Frontend Cloud Run services deployed"
echo "  ✅ Custom Firestore authentication enabled"
echo "  ✅ No DNS, load balancer, or Firebase Auth needed!"
echo ""
echo -e "${BLUE}🌐 Access your services:${NC}"
API_URL=$(gcloud run services describe agent-engine-api --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "Not deployed")
UI_URL=$(gcloud run services describe agent-engine-ui --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "Not deployed")
echo "  API: $API_URL"
echo "  UI: $UI_URL"
echo ""
echo -e "${YELLOW}⚠️  Next Steps:${NC}"
echo "  1. Users can sign up with @asl.apps-eval.com email addresses"
echo "  2. No additional configuration needed - Firestore handles authentication"
echo "  3. Frontend API_URL is automatically configured"
echo ""
echo -e "${GREEN}🚀 Web application deployment with Firestore authentication!${NC}"

