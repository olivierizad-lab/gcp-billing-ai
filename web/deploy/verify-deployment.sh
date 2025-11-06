#!/bin/bash

# Verification Script for Deployment
# Verifies that all components are correctly deployed and configured

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
DOMAIN="${DOMAIN:-asl.apps-eval.com}"
API_SERVICE="agent-engine-api"
UI_SERVICE="agent-engine-ui"

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ ERROR: PROJECT_ID must be set${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Verifying Deployment${NC}"
echo -e "${BLUE}======================${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Domain: $DOMAIN"
echo ""

ERRORS=0

# Check APIs
echo -e "${BLUE}1. Checking Required APIs...${NC}"
REQUIRED_APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "firestore.googleapis.com"
    "bigquery.googleapis.com"
    "aiplatform.googleapis.com"
    "logging.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --project="$PROJECT_ID" --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo -e "${GREEN}  ✅ $api enabled${NC}"
    else
        echo -e "${RED}  ❌ $api not enabled${NC}"
        ((ERRORS++))
    fi
done
echo ""

# Check Service Accounts
echo -e "${BLUE}2. Checking Service Accounts...${NC}"
API_SA="agent-engine-api-sa@$PROJECT_ID.iam.gserviceaccount.com"
UI_SA="agent-engine-ui-sa@$PROJECT_ID.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "$API_SA" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${GREEN}  ✅ $API_SA exists${NC}"
else
    echo -e "${RED}  ❌ $API_SA not found${NC}"
    ((ERRORS++))
fi

if gcloud iam service-accounts describe "$UI_SA" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${GREEN}  ✅ $UI_SA exists${NC}"
else
    echo -e "${RED}  ❌ $UI_SA not found${NC}"
    ((ERRORS++))
fi
echo ""

# Check Custom IAM Role
echo -e "${BLUE}3. Checking Custom IAM Role...${NC}"
CUSTOM_ROLE_ID="gcpBillingAgentService"
if gcloud iam roles describe "$CUSTOM_ROLE_ID" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Custom role $CUSTOM_ROLE_ID exists${NC}"
else
    echo -e "${RED}  ❌ Custom role $CUSTOM_ROLE_ID not found${NC}"
    ((ERRORS++))
fi
echo ""

# Check Firestore
echo -e "${BLUE}4. Checking Firestore Database...${NC}"
if gcloud firestore databases describe --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Firestore database exists${NC}"
else
    echo -e "${RED}  ❌ Firestore database not found${NC}"
    ((ERRORS++))
fi
echo ""

# Check Cloud Run Services
echo -e "${BLUE}5. Checking Cloud Run Services...${NC}"
if gcloud run services describe "$API_SERVICE" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${GREEN}  ✅ $API_SERVICE deployed${NC}"
    API_URL=$(gcloud run services describe "$API_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)")
    echo -e "${BLUE}     URL: $API_URL${NC}"
else
    echo -e "${RED}  ❌ $API_SERVICE not deployed${NC}"
    ((ERRORS++))
fi

if gcloud run services describe "$UI_SERVICE" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${GREEN}  ✅ $UI_SERVICE deployed${NC}"
    UI_URL=$(gcloud run services describe "$UI_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)")
    echo -e "${BLUE}     URL: $UI_URL${NC}"
else
    echo -e "${RED}  ❌ $UI_SERVICE not deployed${NC}"
    ((ERRORS++))
fi
echo ""

# Check IAM Policy Bindings
echo -e "${BLUE}6. Checking IAM Policy Bindings...${NC}"
API_POLICY=$(gcloud run services get-iam-policy "$API_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="json" 2>/dev/null || echo "{}")
UI_POLICY=$(gcloud run services get-iam-policy "$UI_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="json" 2>/dev/null || echo "{}")

# Check if domain is in the policy
if echo "$API_POLICY" | grep -q "domain:$DOMAIN" || echo "$API_POLICY" | grep -q "allAuthenticatedUsers"; then
    echo -e "${GREEN}  ✅ API service has access control configured${NC}"
else
    echo -e "${YELLOW}  ⚠️  API service may not have domain access control (check manually)${NC}"
fi

if echo "$UI_POLICY" | grep -q "domain:$DOMAIN" || echo "$UI_POLICY" | grep -q "allAuthenticatedUsers"; then
    echo -e "${GREEN}  ✅ UI service has access control configured${NC}"
else
    echo -e "${YELLOW}  ⚠️  UI service may not have domain access control (check manually)${NC}"
fi
echo ""

# Check Service Account Permissions
echo -e "${BLUE}7. Checking Service Account Permissions...${NC}"
API_SA_PERMS=$(gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:$API_SA" \
    --format="value(bindings.role)" 2>/dev/null || echo "")

if echo "$API_SA_PERMS" | grep -q "gcpBillingAgentService"; then
    echo -e "${GREEN}  ✅ API service account has custom role${NC}"
else
    echo -e "${YELLOW}  ⚠️  API service account may not have custom role (check manually)${NC}"
fi

if echo "$API_SA_PERMS" | grep -q "logging.logWriter"; then
    echo -e "${GREEN}  ✅ API service account has logging permissions${NC}"
else
    echo -e "${YELLOW}  ⚠️  API service account may not have logging permissions${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}📊 Verification Summary${NC}"
echo -e "${BLUE}======================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo -e "${BLUE}🌐 Service URLs:${NC}"
    if [ -n "$API_URL" ]; then
        echo "  API: $API_URL"
    fi
    if [ -n "$UI_URL" ]; then
        echo "  UI: $UI_URL"
    fi
    echo ""
    echo -e "${YELLOW}📝 Next Steps:${NC}"
    echo "  1. Test access with a user from $DOMAIN"
    echo "  2. Verify agents are deployed and configured"
    echo "  3. Check Cloud Run logs for any errors"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS error(s)${NC}"
    echo ""
    echo -e "${YELLOW}💡 To fix:${NC}"
    echo "  Run: make deploy-all-automated PROJECT_ID=$PROJECT_ID"
    exit 1
fi

