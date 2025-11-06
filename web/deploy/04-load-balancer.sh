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

# Check for yq
if ! command -v yq &> /dev/null
then
    echo -e "${RED}❌ ERROR: yq is not installed.${NC}"
    echo -e "${YELLOW}Please install yq: https://github.com/mikefarah/yq#install${NC}"
    exit 1
fi

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
    gcloud compute network-endpoint-groups create agent-engine-api-neg \
        --network-endpoint-type=SERVERLESS \
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
    gcloud compute network-endpoint-groups create agent-engine-ui-neg \
        --network-endpoint-type=SERVERLESS \
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
URL_MAP_NAME="agent-engine-url-map"
DEFAULT_SERVICE="agent-engine-ui-backend"
API_BACKEND="agent-engine-api-backend"
DEFAULT_SERVICE_URL="projects/$PROJECT_ID/global/backendServices/$DEFAULT_SERVICE"
API_BACKEND_URL="projects/$PROJECT_ID/global/backendServices/$API_BACKEND"

# Check if URL map exists, if not, create a basic one
if ! gcloud compute url-maps describe "$URL_MAP_NAME" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${BLUE}   Creating new ${URL_MAP_NAME}...${NC}"
    gcloud compute url-maps create "$URL_MAP_NAME" \
        --default-service="$DEFAULT_SERVICE_URL" \
        --global \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ ${URL_MAP_NAME} created${NC}"
else
    echo -e "${YELLOW}⚠️  ${URL_MAP_NAME} already exists, updating...${NC}"
fi

# Get fingerprint for update (required to avoid conflicts)
FINGERPRINT=$(gcloud compute url-maps describe "$URL_MAP_NAME" --global --project="$PROJECT_ID" --format="value(fingerprint)")

# Describe the URL map, modify it with yq, and import it back
gcloud compute url-maps describe "$URL_MAP_NAME" --global --project="$PROJECT_ID" --format=yaml > url_map_config.yaml

# Use yq to add/update path matchers and rules robustly
# Ensure defaultService uses full URL format
yq eval '.defaultService = "projects/'"$PROJECT_ID"'/global/backendServices/'"$DEFAULT_SERVICE"'" |
.pathMatchers = ([.pathMatchers[]?, {"name": "api-matcher", "defaultService": "projects/'"$PROJECT_ID"'/global/backendServices/'"$DEFAULT_SERVICE"'", "pathRules": [{"paths": ["/api/*"], "service": "projects/'"$PROJECT_ID"'/global/backendServices/'"$API_BACKEND"'"}]}]) |
.pathMatchers |= unique_by(.name) |
del(.id) |
del(.fingerprint)
' url_map_config.yaml > url_map_config_modified.yaml

# Import with fingerprint flag to avoid the warning
gcloud compute url-maps import "$URL_MAP_NAME" \
    --source=url_map_config_modified.yaml \
    --global \
    --fingerprint="$FINGERPRINT" \
    --project="$PROJECT_ID"

rm url_map_config.yaml url_map_config_modified.yaml

echo -e "${GREEN}✅ ${URL_MAP_NAME} configured${NC}"

echo ""

echo -e "${BLUE}5. Creating Global IP Address...${NC}"
if gcloud compute addresses describe "agent-engine-lb-ip" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  agent-engine-lb-ip already exists, skipping...${NC}"
else
    gcloud compute addresses create agent-engine-lb-ip \
        --global \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ agent-engine-lb-ip created${NC}"
fi

echo ""

echo -e "${BLUE}6. Setting up Google Cloud DNS...${NC}"
if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "agent-engine.example.com" ]; then
    echo -e "${YELLOW}⚠️  DOMAIN not set or using default, skipping DNS setup${NC}"
    echo -e "${YELLOW}   Set DOMAIN environment variable to enable DNS automation${NC}"
    DNS_SETUP=false
else
    # Enable Cloud DNS API
    echo -e "${BLUE}   Enabling Cloud DNS API...${NC}"
    gcloud services enable dns.googleapis.com --project="$PROJECT_ID" --quiet 2>/dev/null || true
    
    # Get the load balancer IP
    LOAD_BALANCER_IP=$(gcloud compute addresses describe "agent-engine-lb-ip" --global --project="$PROJECT_ID" --format="value(address)" 2>/dev/null || echo "")
    
    if [ -z "$LOAD_BALANCER_IP" ]; then
        echo -e "${YELLOW}⚠️  Load balancer IP not found, DNS setup will be skipped${NC}"
        DNS_SETUP=false
    else
        # Extract root domain (e.g., apps-eval.com from asl.apps-eval.com)
        ROOT_DOMAIN=$(echo "$DOMAIN" | sed 's/^[^.]*\.//')
        ZONE_NAME=$(echo "$ROOT_DOMAIN" | tr '.' '-')
        
        echo -e "${BLUE}   Root domain: $ROOT_DOMAIN${NC}"
        echo -e "${BLUE}   Zone name: $ZONE_NAME${NC}"
        echo -e "${BLUE}   Load balancer IP: $LOAD_BALANCER_IP${NC}"
        
        # Check if managed zone exists
        if gcloud dns managed-zones describe "$ZONE_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  DNS managed zone '$ZONE_NAME' already exists${NC}"
        else
            echo -e "${BLUE}   Creating DNS managed zone...${NC}"
            gcloud dns managed-zones create "$ZONE_NAME" \
                --dns-name="$ROOT_DOMAIN" \
                --description="Managed zone for $DOMAIN" \
                --visibility=public \
                --project="$PROJECT_ID"
            echo -e "${GREEN}✅ DNS managed zone created${NC}"
            echo -e "${YELLOW}⚠️  IMPORTANT: Update your domain registrar with these nameservers:${NC}"
            gcloud dns managed-zones describe "$ZONE_NAME" --project="$PROJECT_ID" --format="value(nameServers)" | tr ';' '\n' | sed 's/^/  /'
        fi
        
        # Create or update A record
        echo -e "${BLUE}   Creating/updating A record for $DOMAIN...${NC}"
        # Check if record exists
        EXISTING_RECORD=$(gcloud dns record-sets list \
            --zone="$ZONE_NAME" \
            --name="$DOMAIN." \
            --type=A \
            --project="$PROJECT_ID" \
            --format="value(name)" 2>/dev/null || echo "")
        
        if [ -n "$EXISTING_RECORD" ]; then
            # Update existing record
            gcloud dns record-sets update "$DOMAIN." \
                --zone="$ZONE_NAME" \
                --type=A \
                --rrdatas="$LOAD_BALANCER_IP" \
                --ttl=300 \
                --project="$PROJECT_ID"
            echo -e "${GREEN}✅ A record updated${NC}"
        else
            # Create new record
            gcloud dns record-sets create "$DOMAIN." \
                --zone="$ZONE_NAME" \
                --type=A \
                --rrdatas="$LOAD_BALANCER_IP" \
                --ttl=300 \
                --project="$PROJECT_ID"
            echo -e "${GREEN}✅ A record created${NC}"
        fi
        
        DNS_SETUP=true
    fi
fi

echo ""

echo -e "${BLUE}7. Creating SSL Certificate...${NC}"
if gcloud compute ssl-certificates describe "agent-engine-ssl-cert" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  agent-engine-ssl-cert already exists, skipping...${NC}"
else
    if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "agent-engine.example.com" ]; then
        echo -e "${RED}❌ ERROR: DOMAIN must be set for SSL certificate creation${NC}"
        echo -e "${YELLOW}Set DOMAIN environment variable: export DOMAIN=your-domain.com${NC}"
        exit 1
    fi
    echo -e "${BLUE}   Creating Google-managed SSL certificate...${NC}"
    echo -e "${YELLOW}   Note: Certificate provisioning may take 10-60 minutes after DNS is configured${NC}"
    gcloud compute ssl-certificates create agent-engine-ssl-cert \
        --global \
        --domains="$DOMAIN" \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ agent-engine-ssl-cert created${NC}"
    if [ "$DNS_SETUP" = true ]; then
        echo -e "${YELLOW}   SSL certificate will be automatically provisioned once DNS propagates${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Configure DNS to point $DOMAIN to the load balancer IP for SSL to work${NC}"
    fi
fi

echo ""

echo -e "${BLUE}8. Creating HTTPS Proxy...${NC}"

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

echo -e "${BLUE}9. Creating Forwarding Rule...${NC}"

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

echo -e "${BLUE}10. Setting up IAP (Identity-Aware Proxy)...${NC}"

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
# Note: IAP OAuth clients are created automatically when IAP is enabled
# This section checks and creates if needed
if ! gcloud iap oauth-clients list --project="$PROJECT_ID" 2>/dev/null | grep -q "agent-engine-iap-client"; then
    echo -e "${BLUE}   Creating IAP OAuth client...${NC}"
    IAP_CLIENT=$(gcloud iap oauth-clients create \
        --display_name="Agent Engine IAP Client" \
        --project="$PROJECT_ID" \
        --format="value(name)" 2>/dev/null || echo "")
    if [ -n "$IAP_CLIENT" ]; then
        echo -e "${GREEN}✅ IAP client created: $IAP_CLIENT${NC}"
    else
        echo -e "${YELLOW}⚠️  IAP client creation skipped (may already exist or API not ready)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  IAP client already exists, skipping...${NC}"
fi

echo ""

echo -e "${BLUE}11. Granting IAP Access...${NC}"
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

