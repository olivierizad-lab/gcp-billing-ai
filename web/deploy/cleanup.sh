#!/bin/bash

# Cleanup Script - Remove all deployed resources
# Perfect for cleaning up after a course/temporary deployment

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

echo -e "${BLUE}🧹 Cleanup Script${NC}"
echo -e "${BLUE}=================${NC}"
echo ""
echo -e "${YELLOW}This will delete all deployed resources:${NC}"
echo "  - Cloud Run services (API and UI)"
echo "  - Service Accounts"
echo "  - Infrastructure (VPC, connectors, etc.)"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo ""

read -p "Are you sure you want to delete everything? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Cleanup cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Starting cleanup...${NC}"
echo ""

# Cloud Run Services
echo -e "${BLUE}1. Deleting Cloud Run Services...${NC}"
gcloud run services delete agent-engine-api --region="$REGION" --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  API service not found (already deleted?)${NC}"
gcloud run services delete agent-engine-ui --region="$REGION" --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  UI service not found (already deleted?)${NC}"
echo -e "${GREEN}✅ Cloud Run services deleted${NC}"
echo ""

# Service Accounts
echo -e "${BLUE}2. Deleting Service Accounts...${NC}"
gcloud iam service-accounts delete "agent-engine-api-sa@$PROJECT_ID.iam.gserviceaccount.com" --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  API service account not found${NC}"
gcloud iam service-accounts delete "agent-engine-ui-sa@$PROJECT_ID.iam.gserviceaccount.com" --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  UI service account not found${NC}"
echo -e "${GREEN}✅ Service accounts deleted${NC}"
echo ""

# VPC Connector (if created)
echo -e "${BLUE}3. Deleting VPC Connector...${NC}"
gcloud vpc-access connectors delete agent-engine-vpc-connector --region="$REGION" --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  VPC connector not found (may not have been created)${NC}"
echo -e "${GREEN}✅ VPC connector deleted${NC}"
echo ""

# VPC Network (if created)
echo -e "${BLUE}4. Deleting VPC Network...${NC}"
gcloud compute networks subnets delete agent-engine-subnet --region="$REGION" --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  Subnet not found${NC}"
gcloud compute networks delete agent-engine-vpc --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  VPC network not found${NC}"
echo -e "${GREEN}✅ VPC network deleted${NC}"
echo ""

# Load Balancer resources (if created)
echo -e "${BLUE}5. Deleting Load Balancer Resources (if any)...${NC}"
gcloud compute forwarding-rules delete agent-engine-forwarding-rule --global --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  Forwarding rule not found${NC}"
gcloud compute target-https-proxies delete agent-engine-proxy --global --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  HTTPS proxy not found${NC}"
gcloud compute url-maps delete agent-engine-url-map --global --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  URL map not found${NC}"
gcloud compute backend-services delete agent-engine-api-backend --global --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  API backend not found${NC}"
gcloud compute backend-services delete agent-engine-ui-backend --global --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  UI backend not found${NC}"
gcloud compute network-endpoint-groups delete agent-engine-api-neg --region="$REGION" --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  API NEG not found${NC}"
gcloud compute network-endpoint-groups delete agent-engine-ui-neg --region="$REGION" --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  UI NEG not found${NC}"
gcloud compute addresses delete agent-engine-lb-ip --global --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  IP address not found${NC}"
gcloud compute ssl-certificates delete agent-engine-ssl-cert --global --project="$PROJECT_ID" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  SSL certificate not found${NC}"
echo -e "${GREEN}✅ Load balancer resources deleted${NC}"
echo ""

# Container images (optional - uncomment if you want to delete images too)
# echo -e "${BLUE}6. Deleting Container Images...${NC}"
# gcloud container images delete "gcr.io/$PROJECT_ID/agent-engine-api:latest" --force-delete-tags --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  API image not found${NC}"
# gcloud container images delete "gcr.io/$PROJECT_ID/agent-engine-ui:latest" --force-delete-tags --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  UI image not found${NC}"
# echo -e "${GREEN}✅ Container images deleted${NC}"
# echo ""

echo -e "${GREEN}🎉 Cleanup Complete!${NC}"
echo ""
echo -e "${BLUE}📋 What was deleted:${NC}"
echo "  ✅ Cloud Run services"
echo "  ✅ Service accounts"
echo "  ✅ VPC infrastructure"
echo "  ✅ Load balancer resources (if any)"
echo ""
echo -e "${YELLOW}ℹ️  Note: Container images in Container Registry are kept${NC}"
echo -e "${YELLOW}   (they don't cost much and can be useful for re-deployment)${NC}"
echo ""

