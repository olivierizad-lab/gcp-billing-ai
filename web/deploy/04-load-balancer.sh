#!/bin/bash

# Load Balancer Setup Script (Part 4 of 4)
# This script creates the load balancer, NEGs, and configures IAP
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
REGION="${REGION:-us-central1}"
DOMAIN="${DOMAIN:-agent-engine.example.com}"  # Update with your domain
API_SERVICE="agent-engine-api"
UI_SERVICE="agent-engine-ui"

echo -e "${BLUE}🌐 Load Balancer Setup (Part 4/4)${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Domain: $DOMAIN"
echo "  API Service: $API_SERVICE"
echo "  UI Service: $UI_SERVICE"
echo ""

echo -e "${BLUE}1. Creating Network Endpoint Groups...${NC}"

# Create API NEG
echo -e "${BLUE}   Creating API NEG...${NC}"
if gcloud compute network-endpoint-groups describe "agent-engine-api-neg" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  agent-engine-api-neg already exists, skipping...${NC}"
else
    gcloud compute network-endpoint-groups create serverless agent-engine-api-neg \
        --region="$REGION" \
        --cloud-run-service="$API_SERVICE" \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ agent-engine-api-neg created${NC}"
fi

# Create UI NEG
echo -e "${BLUE}   Creating UI NEG...${NC}"
if gcloud compute network-endpoint-groups describe "agent-engine-ui-neg" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  agent-engine-ui-neg already exists, skipping...${NC}"
else
    gcloud compute network-endpoint-groups create serverless agent-engine-ui-neg \
        --region="$REGION" \
        --cloud-run-service="$UI_SERVICE" \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ agent-engine-ui-neg created${NC}"
fi

echo ""

echo -e "${BLUE}2. Creating Backend Services...${NC}"

# Create API backend service
echo -e "${BLUE}   Creating API backend service...${NC}"
if gcloud compute backend-services describe "agent-engine-api-backend" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  agent-engine-api-backend already exists, skipping...${NC}"
else
    gcloud compute backend-services create agent-engine-api-backend \
        --global \
        --protocol=HTTP \
        --port-name=http \
        --timeout=300 \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ agent-engine-api-backend created${NC}"
fi

# Create UI backend service
echo -e "${BLUE}   Creating UI backend service...${NC}"
if gcloud compute backend-services describe "agent-engine-ui-backend" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  agent-engine-ui-backend already exists, skipping...${NC}"
else
    gcloud compute backend-services create agent-engine-ui-backend \
        --global \
        --protocol=HTTP \
        --port-name=http \
        --timeout=30 \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ agent-engine-ui-backend created${NC}"
fi

echo ""

echo -e "${BLUE}3. Adding NEGs to Backend Services...${NC}"

# Add NEGs to backend services (idempotent - will skip if already added)
gcloud compute backend-services add-backend agent-engine-api-backend \
    --global \
    --network-endpoint-group="agent-engine-api-neg" \
    --network-endpoint-group-region="$REGION" \
    --project="$PROJECT_ID" 2>/dev/null || echo -e "${YELLOW}⚠️  NEG already added to API backend${NC}"

gcloud compute backend-services add-backend agent-engine-ui-backend \
    --global \
    --network-endpoint-group="agent-engine-ui-neg" \
    --network-endpoint-group-region="$REGION" \
    --project="$PROJECT_ID" 2>/dev/null || echo -e "${YELLOW}⚠️  NEG already added to UI backend${NC}"

echo -e "${GREEN}✅ NEGs added to backend services${NC}"
echo ""

echo -e "${BLUE}4. Creating URL Map with API Routing...${NC}"

# Create URL map
if gcloud compute url-maps describe "agent-engine-url-map" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  agent-engine-url-map already exists, updating...${NC}"
    
    # Update existing URL map to include API routing
    gcloud compute url-maps add-path-matcher agent-engine-url-map \
        --path-matcher-name="api-matcher" \
        --default-service="agent-engine-ui-backend" \
        --global \
        --project="$PROJECT_ID" 2>/dev/null || echo "Path matcher may already exist"
    
    # Add path rules for API
    gcloud compute url-maps add-path-rule agent-engine-url-map \
        --path-matcher-name="api-matcher" \
        --path-rule-service="agent-engine-api-backend" \
        --path-rule-paths="/api/*" \
        --global \
        --project="$PROJECT_ID" 2>/dev/null || echo "Path rule may already exist"
    
    echo -e "${GREEN}✅ agent-engine-url-map updated${NC}"
else
    # Create new URL map
    gcloud compute url-maps create agent-engine-url-map \
        --default-service="agent-engine-ui-backend" \
        --global \
        --project="$PROJECT_ID"
    
    # Add path matcher
    gcloud compute url-maps add-path-matcher agent-engine-url-map \
        --path-matcher-name="api-matcher" \
        --default-service="agent-engine-ui-backend" \
        --global \
        --project="$PROJECT_ID"
    
    # Add path rules for API
    gcloud compute url-maps add-path-rule agent-engine-url-map \
        --path-matcher-name="api-matcher" \
        --path-rule-service="agent-engine-api-backend" \
        --path-rule-paths="/api/*" \
        --global \
        --project="$PROJECT_ID"
    
    echo -e "${GREEN}✅ agent-engine-url-map created${NC}"
fi

echo ""

echo -e "${BLUE}5. Creating HTTPS Proxy...${NC}"

# Create HTTPS proxy
if gcloud compute target-https-proxies describe "agent-engine-proxy" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  agent-engine-proxy already exists, skipping...${NC}"
else
    gcloud compute target-https-proxies create agent-engine-proxy \
        --url-map="agent-engine-url-map" \
        --ssl-certificates="agent-engine-ssl-cert" \
        --global \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ agent-engine-proxy created${NC}"
fi

echo ""

echo -e "${BLUE}6. Creating Forwarding Rule...${NC}"

# Create forwarding rule
if gcloud compute forwarding-rules describe "agent-engine-forwarding-rule" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  agent-engine-forwarding-rule already exists, skipping...${NC}"
else
    gcloud compute forwarding-rules create agent-engine-forwarding-rule \
        --global \
        --target-https-proxy="agent-engine-proxy" \
        --address="agent-engine-lb-ip" \
        --ports=443 \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ agent-engine-forwarding-rule created${NC}"
fi

echo ""

echo -e "${BLUE}7. Setting up IAP (Identity-Aware Proxy)...${NC}"

# Enable IAP on backend services
echo -e "${BLUE}   Enabling IAP on API backend...${NC}"
gcloud compute backend-services update agent-engine-api-backend \
    --global \
    --iap=enabled \
    --project="$PROJECT_ID"

echo -e "${BLUE}   Enabling IAP on UI backend...${NC}"
gcloud compute backend-services update agent-engine-ui-backend \
    --global \
    --iap=enabled \
    --project="$PROJECT_ID"

# Create IAP OAuth client if it doesn't exist
if ! gcloud iap oauth-clients list --project="$PROJECT_ID" 2>/dev/null | grep -q "agent-engine-iap-client"; then
    IAP_CLIENT=$(gcloud iap oauth-clients create \
        --display_name="Agent Engine IAP Client" \
        --project="$PROJECT_ID" \
        --format="value(name)")
    echo -e "${GREEN}✅ IAP client created: $IAP_CLIENT${NC}"
else
    echo -e "${YELLOW}⚠️  IAP client already exists, skipping...${NC}"
fi

echo ""

echo -e "${BLUE}8. Granting IAP Access...${NC}"
echo -e "${YELLOW}⚠️  You need to grant IAP access to users/groups:${NC}"
echo ""
echo "Example - Grant access to a user:"
echo "  gcloud iap web add-iam-policy-binding \\"
echo "    --resource-type=backend-services \\"
echo "    --service=agent-engine-api-backend \\"
echo "    --member='user:user@example.com' \\"
echo "    --role='roles/iap.httpsResourceAccessor' \\"
echo "    --project=$PROJECT_ID"
echo ""
echo "Example - Grant access to all authenticated users:"
echo "  gcloud iap web add-iam-policy-binding \\"
echo "    --resource-type=backend-services \\"
echo "    --service=agent-engine-api-backend \\"
echo "    --member='allAuthenticatedUsers' \\"
echo "    --role='roles/iap.httpsResourceAccessor' \\"
echo "    --project=$PROJECT_ID"
echo ""

# Get final URLs and IP
LOAD_BALANCER_IP=$(gcloud compute addresses describe "agent-engine-lb-ip" --global --project="$PROJECT_ID" --format="value(address)" 2>/dev/null || echo "Not found")
API_URL=$(gcloud run services describe "$API_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "Not found")
UI_URL=$(gcloud run services describe "$UI_SERVICE" --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "Not found")

echo -e "${GREEN}🎉 Load Balancer Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📋 What was configured:${NC}"
echo "  ✅ Network Endpoint Groups: agent-engine-api-neg, agent-engine-ui-neg"
echo "  ✅ Backend Services: agent-engine-api-backend, agent-engine-ui-backend"
echo "  ✅ URL Map: agent-engine-url-map with API routing (/api/*)"
echo "  ✅ HTTPS Proxy: agent-engine-proxy"
echo "  ✅ Forwarding Rule: agent-engine-forwarding-rule"
echo "  ✅ IAP Enabled on both backend services"
echo ""
echo -e "${BLUE}🌐 Final URLs:${NC}"
echo "  Load Balancer IP: $LOAD_BALANCER_IP"
echo "  Secure Frontend: https://$DOMAIN (once DNS configured)"
echo "  API Service: $API_URL"
echo "  UI Service: $UI_URL"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "  1. Configure DNS to point $DOMAIN to $LOAD_BALANCER_IP"
echo "  2. Grant IAP access to users/groups (see commands above)"
echo "  3. Update frontend API_URL to use load balancer domain"
echo ""
echo -e "${BLUE}🔄 All 4 scripts completed successfully!${NC}"
echo "  1. ✅ Infrastructure (VPC, IAM, SSL)"
echo "  2. ✅ IAM Permissions"
echo "  3. ✅ Applications (Cloud Run services)"
echo "  4. ✅ Load Balancer (NEGs, routing, IAP)"
echo ""

