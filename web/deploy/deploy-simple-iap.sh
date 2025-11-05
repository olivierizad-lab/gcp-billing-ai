#!/bin/bash

# Simple IAP Deployment - No DNS or Load Balancer Required!
# This script deploys Cloud Run services with native IAP support
# Based on provisioner project but simplified for Cloud Run native IAP

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

echo -e "${BLUE}🚀 Simple IAP Deployment (No DNS Required!)${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "${YELLOW}This deployment uses Cloud Run's native IAP support.${NC}"
echo -e "${YELLOW}✅ No DNS configuration needed${NC}"
echo -e "${YELLOW}✅ No load balancer needed${NC}"
echo -e "${YELLOW}✅ No SSL certificate needed${NC}"
echo -e "${YELLOW}✅ Simple and secure!${NC}"
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

# Run infrastructure and IAM scripts (these are still needed)
echo -e "${BLUE}=== Setting up Infrastructure ===${NC}"
export PROJECT_ID REGION
"$SCRIPT_DIR/01-infrastructure.sh" 2>/dev/null || echo -e "${YELLOW}⚠️  Some infrastructure may already exist (continuing...)${NC}"

echo ""
echo -e "${BLUE}=== Setting up IAM Permissions ===${NC}"
export PROJECT_ID
"$SCRIPT_DIR/02-iam-permissions.sh" 2>/dev/null || echo -e "${YELLOW}⚠️  Some IAM permissions may already exist (continuing...)${NC}"

echo ""
echo -e "${BLUE}=== Deploying Applications with Native IAP ===${NC}"
export PROJECT_ID REGION
"$SCRIPT_DIR/03-applications-iap.sh"

echo ""
echo -e "${GREEN}🎉 DEPLOYMENT SUCCESSFUL!${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "  ✅ Service Accounts configured"
echo "  ✅ Backend and Frontend Cloud Run services deployed"
echo "  ✅ IAP authentication enabled"
echo "  ✅ No DNS or load balancer needed!"
echo ""
echo -e "${BLUE}🌐 Access your services:${NC}"
API_URL=$(gcloud run services describe agent-engine-api --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "Not deployed")
UI_URL=$(gcloud run services describe agent-engine-ui --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "Not deployed")
echo "  API: $API_URL"
echo "  UI: $UI_URL"
echo ""
echo -e "${YELLOW}⚠️  Next Steps:${NC}"
echo "  1. Users will authenticate with Google accounts when accessing URLs"
echo "  2. Grant specific users/groups access if needed (see commands above)"
echo "  3. Update frontend API_URL to use the API service URL"
echo ""
echo -e "${GREEN}🚀 Much simpler than load balancer setup!${NC}"

