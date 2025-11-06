#!/bin/bash

# Authentication Configuration Script
# This script attempts to automate authentication setup for Cloud Run
# Note: Some OAuth consent screen configuration requires manual steps

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ ERROR: PROJECT_ID must be set${NC}"
    exit 1
fi

echo -e "${BLUE}🔐 Configuring Authentication for Cloud Run${NC}"
echo -e "${BLUE}===========================================${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
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
    read -p "Continue with authentication configuration? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Configuration cancelled.${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${BLUE}1. Enabling Required APIs...${NC}"
# IAP API is required for Cloud Run authentication
gcloud services enable \
    iap.googleapis.com \
    cloudresourcemanager.googleapis.com \
    --project="$PROJECT_ID" \
    --quiet

# OAuth2 API may not be available in all projects (internal service)
if gcloud services enable oauth2.googleapis.com --project="$PROJECT_ID" --quiet 2>/dev/null; then
    echo -e "${GREEN}✅ OAuth2 API enabled${NC}"
else
    echo -e "${YELLOW}⚠️  OAuth2 API not available (may be internal service)${NC}"
    echo -e "${YELLOW}     This is OK - domain restrictions work without it${NC}"
fi

echo -e "${GREEN}✅ IAP API enabled${NC}"
echo ""

echo -e "${BLUE}2. Recommended: Domain-Based Access Control${NC}"
echo -e "${GREEN}✅ For Google Workspace/Cloud Identity organizations:${NC}"
echo "   Use domain restrictions - works immediately, no OAuth consent screen needed!"
echo ""
echo -e "${BLUE}Recommended Approach:${NC}"
echo "  make security-harden \\"
echo "    PROJECT_ID=$PROJECT_ID \\"
echo "    ACCESS_CONTROL_TYPE=domain \\"
echo "    ACCESS_CONTROL_VALUE=your-domain.com"
echo ""
echo -e "${YELLOW}Benefits:${NC}"
echo "  ✅ Works immediately - no manual configuration"
echo "  ✅ More secure - restricted to your domain"
echo "  ✅ Fully automated - can be scripted"
echo "  ✅ No OAuth consent screen needed"
echo ""

echo -e "${BLUE}3. Alternative: OAuth Consent Screen (For External Users)${NC}"
echo -e "${YELLOW}⚠️  Only needed if allowing external Google accounts:${NC}"
echo ""
echo -e "${BLUE}Manual Steps (if needed):${NC}"
echo "  1. Go to: https://console.cloud.google.com/apis/credentials/consent?project=$PROJECT_ID"
echo "  2. Configure OAuth consent screen:"
echo "     - User Type: External"
echo "     - App name: GCP Billing Agent"
echo "     - Support email: your-email@domain.com"
echo "     - Authorized domains: your-domain.com"
echo "  3. Add scopes (if needed):"
echo "     - https://www.googleapis.com/auth/userinfo.email"
echo "     - https://www.googleapis.com/auth/userinfo.profile"
echo "  4. Save and continue"
echo ""
echo -e "${YELLOW}⚠️  Note: OAuth consent screen automation is limited by Google.${NC}"
echo -e "${YELLOW}     For Google Workspace/Cloud Identity, use domain restrictions instead!${NC}"
echo ""

echo -e "${GREEN}✅ Authentication Configuration Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "  1. ✅ APIs enabled"
echo "  2. ${GREEN}⭐ Recommended: Use domain restrictions (see above)${NC}"
echo "  3. ⚠️  Or configure OAuth consent screen manually (if allowing external users)"
echo "  4. ✅ IAM policies will be set by security-hardening script"
echo ""
echo -e "${BLUE}For more details:${NC}"
echo "  - See docs/AUTHENTICATION_SETUP.md"
echo "  - See docs/SECURITY_IMPROVEMENTS.md"
echo ""

