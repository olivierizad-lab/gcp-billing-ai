#!/bin/bash

# Master Deployment Script - Runs all 4 modular scripts in sequence
# This is the main entry point for the complete deployment
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
DOMAIN="${DOMAIN:-agent-engine.example.com}"

echo -e "${BLUE}🚀 Complete Agent Engine Chat Deployment${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "${YELLOW}This will run all 4 modular deployment scripts:${NC}"
echo "  1. Infrastructure (VPC, IAM, SSL)"
echo "  2. IAM Permissions"
echo "  3. Applications (Cloud Run services)"
echo "  4. Load Balancer (NEGs, routing, IAP)"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Domain: $DOMAIN"
echo ""
echo -e "${YELLOW}Each script is idempotent and can be run safely multiple times.${NC}"
echo -e "${YELLOW}You can also run individual scripts if needed.${NC}"
echo ""

read -p "Continue with full deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Starting deployment sequence...${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run each script in sequence
echo -e "${BLUE}=== Running Script 1/4: Infrastructure ===${NC}"
export PROJECT_ID REGION DOMAIN
"$SCRIPT_DIR/01-infrastructure.sh"

echo ""
echo -e "${BLUE}=== Running Script 2/4: IAM Permissions ===${NC}"
export PROJECT_ID
"$SCRIPT_DIR/02-iam-permissions.sh"

echo ""
echo -e "${BLUE}=== Running Script 3/4: Applications ===${NC}"
export PROJECT_ID REGION
"$SCRIPT_DIR/03-applications.sh"

echo ""
echo -e "${BLUE}=== Running Script 4/4: Load Balancer ===${NC}"
export PROJECT_ID REGION DOMAIN
"$SCRIPT_DIR/04-load-balancer.sh"

echo ""
echo -e "${GREEN}🎉 COMPLETE DEPLOYMENT SUCCESSFUL!${NC}"
echo ""
echo -e "${BLUE}📋 Summary of what was deployed:${NC}"
echo "  ✅ VPC Network and Subnet"
echo "  ✅ VPC Connector"
echo "  ✅ Service Accounts with all required permissions"
echo "  ✅ SSL Certificate"
echo "  ✅ Global IP Address"
echo "  ✅ Backend and Frontend Cloud Run services"
echo "  ✅ Network Endpoint Groups"
echo "  ✅ Load Balancer with routing"
echo "  ✅ API routing (/api/* → backend)"
echo "  ✅ IAP Security enabled"
echo ""
echo -e "${BLUE}🌐 Your system is ready at: https://$DOMAIN${NC}"
echo -e "${YELLOW}(Once DNS is configured to point to the load balancer IP)${NC}"
echo ""
echo -e "${YELLOW}⚠️  Next Steps:${NC}"
echo "  1. Configure DNS to point $DOMAIN to the load balancer IP"
echo "  2. Grant IAP access to users/groups"
echo "  3. Update frontend API_URL to use load balancer domain"
echo ""
echo -e "${GREEN}🚀 No more deployment state issues! Everything is in scripts!${NC}"

