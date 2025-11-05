#!/bin/bash

# Infrastructure Deployment Script (Part 1 of 4)
# This script creates the basic infrastructure: VPC, IAM, SSL, etc.
# Based on provisioner project deployment pattern

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - Update these for your project
PROJECT_ID="${PROJECT_ID:-qwiklabs-asl-04-8e9f23e85ced}"
REGION="${REGION:-us-central1}"
DOMAIN="${DOMAIN:-agent-engine.example.com}"  # Update with your domain

# Resource names
VPC_NAME="agent-engine-vpc"
SUBNET_NAME="agent-engine-subnet"
VPC_CONNECTOR_NAME="agent-engine-vpc-connector"
LOAD_BALANCER_NAME="agent-engine-lb"
API_SERVICE_ACCOUNT="agent-engine-api-sa"
FRONTEND_SERVICE_ACCOUNT="agent-engine-ui-sa"

echo -e "${BLUE}🏗️  Infrastructure Deployment (Part 1/4)${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Domain: $DOMAIN"
echo ""

# Function to check if resource exists
resource_exists() {
    local resource_type="$1"
    local resource_name="$2"
    
    case "$resource_type" in
        "network")
            gcloud compute networks describe "$resource_name" --project="$PROJECT_ID" >/dev/null 2>&1
            ;;
        "subnet")
            gcloud compute networks subnets describe "$resource_name" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1
            ;;
        "vpc-connector")
            gcloud vpc-access connectors describe "$resource_name" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1
            ;;
        "service-account")
            gcloud iam service-accounts describe "$resource_name@$PROJECT_ID.iam.gserviceaccount.com" --project="$PROJECT_ID" >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}

echo -e "${BLUE}1. Enabling Required APIs...${NC}"
gcloud services enable \
    compute.googleapis.com \
    run.googleapis.com \
    vpcaccess.googleapis.com \
    iap.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com \
    --project="$PROJECT_ID"

echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

echo -e "${BLUE}2. Creating VPC Network...${NC}"
if resource_exists "network" "$VPC_NAME"; then
    echo -e "${YELLOW}⚠️  $VPC_NAME already exists, skipping...${NC}"
else
    gcloud compute networks create "$VPC_NAME" \
        --subnet-mode=custom \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ $VPC_NAME created${NC}"
fi

echo ""

echo -e "${BLUE}3. Creating Subnet...${NC}"
if resource_exists "subnet" "$SUBNET_NAME"; then
    echo -e "${YELLOW}⚠️  $SUBNET_NAME already exists, skipping...${NC}"
else
    gcloud compute networks subnets create "$SUBNET_NAME" \
        --network="$VPC_NAME" \
        --range=10.0.0.0/24 \
        --region="$REGION" \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ $SUBNET_NAME created${NC}"
fi

echo ""

echo -e "${BLUE}4. Creating VPC Connector...${NC}"
if resource_exists "vpc-connector" "$VPC_CONNECTOR_NAME"; then
    echo -e "${YELLOW}⚠️  $VPC_CONNECTOR_NAME already exists, skipping...${NC}"
else
    gcloud vpc-access connectors create "$VPC_CONNECTOR_NAME" \
        --network="$VPC_NAME" \
        --range=10.8.0.0/28 \
        --region="$REGION" \
        --min-instances=2 \
        --max-instances=3 \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ $VPC_CONNECTOR_NAME created${NC}"
fi

echo ""

echo -e "${BLUE}5. Creating Service Accounts...${NC}"
if resource_exists "service-account" "$API_SERVICE_ACCOUNT"; then
    echo -e "${YELLOW}⚠️  $API_SERVICE_ACCOUNT already exists, skipping...${NC}"
else
    gcloud iam service-accounts create "$API_SERVICE_ACCOUNT" \
        --display-name='Agent Engine API Service Account' \
        --description='Service account for Agent Engine API backend' \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ $API_SERVICE_ACCOUNT created${NC}"
fi

if resource_exists "service-account" "$FRONTEND_SERVICE_ACCOUNT"; then
    echo -e "${YELLOW}⚠️  $FRONTEND_SERVICE_ACCOUNT already exists, skipping...${NC}"
else
    gcloud iam service-accounts create "$FRONTEND_SERVICE_ACCOUNT" \
        --display-name='Agent Engine UI Service Account' \
        --description='Service account for Agent Engine frontend' \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ $FRONTEND_SERVICE_ACCOUNT created${NC}"
fi

echo ""

echo -e "${BLUE}6. Creating Global IP Address...${NC}"
if gcloud compute addresses describe "$LOAD_BALANCER_NAME-ip" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  $LOAD_BALANCER_NAME-ip already exists, skipping...${NC}"
else
    gcloud compute addresses create "$LOAD_BALANCER_NAME-ip" \
        --global \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ $LOAD_BALANCER_NAME-ip created${NC}"
fi

echo ""

echo -e "${BLUE}7. Creating SSL Certificate...${NC}"
if gcloud compute ssl-certificates describe "agent-engine-ssl-cert" --global --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  agent-engine-ssl-cert already exists, skipping...${NC}"
else
    gcloud compute ssl-certificates create agent-engine-ssl-cert \
        --global \
        --domains="$DOMAIN" \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ agent-engine-ssl-cert created${NC}"
fi

echo ""

echo -e "${GREEN}🎉 Infrastructure Part 1 Complete!${NC}"
echo ""
echo -e "${BLUE}📋 What was created:${NC}"
echo "  ✅ APIs enabled"
echo "  ✅ VPC Network: $VPC_NAME"
echo "  ✅ Subnet: $SUBNET_NAME"
echo "  ✅ VPC Connector: $VPC_CONNECTOR_NAME"
echo "  ✅ Service Accounts: $API_SERVICE_ACCOUNT, $FRONTEND_SERVICE_ACCOUNT"
echo "  ✅ Global IP: $LOAD_BALANCER_NAME-ip"
echo "  ✅ SSL Certificate: agent-engine-ssl-cert"
echo ""
echo -e "${BLUE}🔄 Next steps:${NC}"
echo "  1. Run: ./web/deploy/02-iam-permissions.sh"
echo "  2. Run: ./web/deploy/03-applications.sh"
echo "  3. Run: ./web/deploy/04-load-balancer.sh"
echo ""

