#!/bin/bash

# Security Hardening Script (Part 5 of deployment)
# This script implements security improvements:
# 1. Replaces allAuthenticatedUsers with Cloud Identity-based access
# 2. Creates custom IAM role with least privilege
# 3. Consolidates service accounts

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
API_SERVICE="agent-engine-api"
UI_SERVICE="agent-engine-ui"

# Access control configuration
# Option 1: Domain restriction (recommended)
# ACCESS_CONTROL_TYPE="domain"
# ACCESS_CONTROL_VALUE="asl.apps-eval.com"

# Option 2: Group-based access
# ACCESS_CONTROL_TYPE="group"
# ACCESS_CONTROL_VALUE="billing-users@asl.apps-eval.com"

# Option 3: Individual users (comma-separated)
# ACCESS_CONTROL_TYPE="users"
# ACCESS_CONTROL_VALUE="user1@asl.apps-eval.com,user2@asl.apps-eval.com"

# Option 4: Keep allAuthenticatedUsers (default, less secure)
# Defaults to domain: asl.apps-eval.com for testing
ACCESS_CONTROL_TYPE="${ACCESS_CONTROL_TYPE:-domain}"
ACCESS_CONTROL_VALUE="${ACCESS_CONTROL_VALUE:-asl.apps-eval.com}"

echo -e "${BLUE}🔐 Security Hardening Script${NC}"
echo -e "${BLUE}============================${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Access Control Type: $ACCESS_CONTROL_TYPE"
if [ -n "$ACCESS_CONTROL_VALUE" ]; then
  echo "  Access Control Value: $ACCESS_CONTROL_VALUE"
fi
echo ""



echo ""
echo -e "${BLUE}1. Creating Custom IAM Role...${NC}"

CUSTOM_ROLE_ID="gcpBillingAgentService"
CUSTOM_ROLE_NAME="projects/$PROJECT_ID/roles/$CUSTOM_ROLE_ID"

# Check if role already exists
if gcloud iam roles describe "$CUSTOM_ROLE_ID" --project="$PROJECT_ID" &>/dev/null; then
    echo -e "${YELLOW}⚠️  Custom role already exists. Updating...${NC}"
    gcloud iam roles update "$CUSTOM_ROLE_ID" \
        --project="$PROJECT_ID" \
        --file="$(dirname "$0")/custom-iam-role.yaml" \
        --quiet
    echo -e "${GREEN}✅ Custom role updated${NC}"
else
    echo -e "${BLUE}Creating new custom role...${NC}"
    gcloud iam roles create "$CUSTOM_ROLE_ID" \
        --project="$PROJECT_ID" \
        --file="$(dirname "$0")/custom-iam-role.yaml" \
        --quiet
    echo -e "${GREEN}✅ Custom role created${NC}"
fi

echo ""
echo -e "${BLUE}2. Updating Service Account with Custom Role...${NC}"

API_SERVICE_ACCOUNT="agent-engine-api-sa@$PROJECT_ID.iam.gserviceaccount.com"

# Remove old role bindings (if they exist)
echo -e "${YELLOW}Removing old role bindings...${NC}"
for role in "roles/bigquery.dataViewer" "roles/bigquery.jobUser" "roles/aiplatform.user" "roles/datastore.user"; do
    gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$API_SERVICE_ACCOUNT" \
        --role="$role" \
        --quiet 2>/dev/null || echo -e "${YELLOW}  ⚠️  Role $role not found (may have been removed)${NC}"
done

# Add custom role
echo -e "${BLUE}Adding custom role...${NC}"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$API_SERVICE_ACCOUNT" \
    --role="$CUSTOM_ROLE_NAME" \
    --quiet

# Keep logging role (needed for Cloud Run)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$API_SERVICE_ACCOUNT" \
    --role="roles/logging.logWriter" \
    --quiet

echo -e "${GREEN}✅ Service account updated with custom role${NC}"

echo ""
echo -e "${BLUE}3. Updating Cloud Run Access Control...${NC}"

# Function to add access control binding
add_access_control() {
    local service=$1
    local member=$2
    
    echo -e "${BLUE}Adding access for $member to $service...${NC}"
    gcloud run services add-iam-policy-binding "$service" \
        --region="$REGION" \
        --member="$member" \
        --role="roles/run.invoker" \
        --project="$PROJECT_ID" \
        --quiet
}

# Remove allAuthenticatedUsers and allUsers from both services
echo -e "${YELLOW}Removing allAuthenticatedUsers and allUsers access...${NC}"
for member in "allAuthenticatedUsers" "allUsers"; do
    gcloud run services remove-iam-policy-binding "$API_SERVICE" \
        --region="$REGION" \
        --member="$member" \
        --role="roles/run.invoker" \
        --project="$PROJECT_ID" \
        --quiet 2>/dev/null || echo -e "${YELLOW}  ⚠️  $member not found on API service${NC}"

    gcloud run services remove-iam-policy-binding "$UI_SERVICE" \
        --region="$REGION" \
        --member="$member" \
        --role="roles/run.invoker" \
        --project="$PROJECT_ID" \
        --quiet 2>/dev/null || echo -e "${YELLOW}  ⚠️  $member not found on UI service${NC}"
done

# Add new access control based on type
if [ "$ACCESS_CONTROL_TYPE" = "domain" ]; then
    if [ -z "$ACCESS_CONTROL_VALUE" ]; then
        echo -e "${RED}❌ ERROR: ACCESS_CONTROL_VALUE must be set for domain access control${NC}"
        exit 1
    fi
    add_access_control "$API_SERVICE" "domain:$ACCESS_CONTROL_VALUE"
    add_access_control "$UI_SERVICE" "domain:$ACCESS_CONTROL_VALUE"
    
elif [ "$ACCESS_CONTROL_TYPE" = "group" ]; then
    if [ -z "$ACCESS_CONTROL_VALUE" ]; then
        echo -e "${RED}❌ ERROR: ACCESS_CONTROL_VALUE must be set for group access control${NC}"
        exit 1
    fi
    add_access_control "$API_SERVICE" "group:$ACCESS_CONTROL_VALUE"
    add_access_control "$UI_SERVICE" "group:$ACCESS_CONTROL_VALUE"
    
elif [ "$ACCESS_CONTROL_TYPE" = "users" ]; then
    if [ -z "$ACCESS_CONTROL_VALUE" ]; then
        echo -e "${RED}❌ ERROR: ACCESS_CONTROL_VALUE must be set for users access control${NC}"
        exit 1
    fi
    # Split comma-separated users
    IFS=',' read -ra USERS <<< "$ACCESS_CONTROL_VALUE"
    for user in "${USERS[@]}"; do
        user=$(echo "$user" | xargs)  # Trim whitespace
        add_access_control "$API_SERVICE" "user:$user"
        add_access_control "$UI_SERVICE" "user:$user"
    done
    
elif [ "$ACCESS_CONTROL_TYPE" = "allAuthenticatedUsers" ]; then
    echo -e "${YELLOW}⚠️  Keeping allAuthenticatedUsers (less secure)${NC}"
    add_access_control "$API_SERVICE" "allAuthenticatedUsers"
    add_access_control "$UI_SERVICE" "allAuthenticatedUsers"
    
else
    echo -e "${RED}❌ ERROR: Unknown ACCESS_CONTROL_TYPE: $ACCESS_CONTROL_TYPE${NC}"
    echo -e "${YELLOW}Valid options: domain, group, users, allAuthenticatedUsers${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Access control updated${NC}"

echo ""
echo -e "${GREEN}🎉 Security Hardening Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "  ✅ Custom IAM role created/updated: $CUSTOM_ROLE_NAME"
echo "  ✅ Service account updated with custom role"
echo "  ✅ Old role bindings removed"
echo "  ✅ Cloud Run access control updated"
echo ""
echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo "  1. Test access with your configured users/groups"
echo "  2. Monitor logs for any access issues"
echo "  3. If issues arise, you can temporarily re-add allAuthenticatedUsers"
echo ""
echo -e "${BLUE}🔍 To verify access control:${NC}"
echo "  gcloud run services get-iam-policy $API_SERVICE --region=$REGION --project=$PROJECT_ID"
echo "  gcloud run services get-iam-policy $UI_SERVICE --region=$REGION --project=$PROJECT_ID"
echo ""
echo -e "${BLUE}🔄 To rollback to allAuthenticatedUsers:${NC}"
echo "  export ACCESS_CONTROL_TYPE=allAuthenticatedUsers"
echo "  ./05-security-hardening.sh"

