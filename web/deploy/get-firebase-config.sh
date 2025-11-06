#!/bin/bash

# Script to automatically fetch Firebase configuration values
# This tries multiple methods to get Firebase web app config

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ID="${PROJECT_ID:-qwiklabs-asl-04-8e9f23e85ced}"

echo -e "${BLUE}🔍 Fetching Firebase Configuration${NC}"
echo -e "${BLUE}===================================${NC}"
echo ""
echo "Project ID: $PROJECT_ID"
echo ""

# Method 1: Try Firebase CLI
if command -v firebase &> /dev/null; then
    echo -e "${BLUE}Method 1: Trying Firebase CLI...${NC}"
    if firebase projects:list 2>/dev/null | grep -q "$PROJECT_ID"; then
        echo -e "${GREEN}✅ Firebase CLI found and project is accessible${NC}"
        # Try to get web app config
        # Note: Firebase CLI doesn't have a direct command for this, but we can try
        echo -e "${YELLOW}⚠️  Firebase CLI doesn't provide direct web app config access${NC}"
        echo -e "${YELLOW}   You'll need to get this from Firebase Console${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Firebase CLI not installed${NC}"
    echo -e "${YELLOW}   Install with: npm install -g firebase-tools${NC}"
fi

echo ""

# Method 2: Try to get from Firebase REST API
echo -e "${BLUE}Method 2: Trying Firebase REST API...${NC}"

# Get access token
ACCESS_TOKEN=$(gcloud auth print-access-token 2>/dev/null || echo "")

if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}❌ Could not get access token${NC}"
else
    echo -e "${GREEN}✅ Got access token${NC}"
    
    # Try to get Firebase project info
    # Note: Firebase Admin API might not expose web app config directly
    # We'll try the Firebase Management API
    echo -e "${BLUE}   Attempting to fetch web app config...${NC}"
    
    # Get project number (needed for some APIs)
    PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null || echo "")
    
    if [ -n "$PROJECT_NUMBER" ]; then
        echo -e "${GREEN}✅ Project Number: $PROJECT_NUMBER${NC}"
        
        # Try Firebase Management API to list web apps
        # This requires the Firebase Management API to be enabled
        WEB_APPS=$(curl -s -X GET \
            "https://firebase.googleapis.com/v1beta1/projects/$PROJECT_ID/webApps" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" 2>/dev/null || echo "")
        
        if [ -n "$WEB_APPS" ] && echo "$WEB_APPS" | grep -q "appId"; then
            echo -e "${GREEN}✅ Found web apps!${NC}"
            echo "$WEB_APPS" | jq -r '.apps[] | "App ID: \(.appId)\nDisplay Name: \(.displayName)"' 2>/dev/null || echo "$WEB_APPS"
        else
            echo -e "${YELLOW}⚠️  Could not fetch web apps via API${NC}"
            echo -e "${YELLOW}   This might require Firebase Management API to be enabled${NC}"
        fi
    fi
fi

echo ""

# Method 3: Provide instructions for manual retrieval
echo -e "${BLUE}Method 3: Manual Retrieval Instructions${NC}"
echo -e "${YELLOW}=====================================${NC}"
echo ""
echo "To get Firebase web app configuration:"
echo ""
echo "1. Go to Firebase Console:"
echo "   https://console.firebase.google.com/project/$PROJECT_ID"
echo ""
echo "2. Click on the gear icon (⚙️) > Project Settings"
echo ""
echo "3. Scroll down to 'Your apps' section"
echo ""
echo "4. If you don't have a web app yet:"
echo "   - Click the 'Web' icon (</>)"
echo "   - Register your app (e.g., 'GCP Billing Agent')"
echo "   - Copy the config values"
echo ""
echo "5. If you already have a web app:"
echo "   - Click on the app"
echo "   - Copy the config values from the code snippet"
echo ""
echo "6. The config will look like this:"
echo ""
echo "   const firebaseConfig = {"
echo "     apiKey: \"AIza...\","
echo "     authDomain: \"$PROJECT_ID.firebaseapp.com\","
echo "     projectId: \"$PROJECT_ID\","
echo "     storageBucket: \"$PROJECT_ID.appspot.com\","
echo "     messagingSenderId: \"123456789\","
echo "     appId: \"1:123456789:web:abc123\""
echo "   };"
echo ""
echo "7. Extract the values:"
echo "   - FIREBASE_API_KEY = apiKey value"
echo "   - FIREBASE_MESSAGING_SENDER_ID = messagingSenderId value"
echo "   - FIREBASE_APP_ID = appId value"
echo ""

# Method 4: Try to check if web app exists and provide direct link
echo -e "${BLUE}Method 4: Checking for existing web apps...${NC}"

# Enable Firebase APIs
echo -e "${BLUE}   Enabling Firebase APIs...${NC}"
gcloud services enable firebase.googleapis.com --project="$PROJECT_ID" --quiet 2>/dev/null || true
gcloud services enable identitytoolkit.googleapis.com --project="$PROJECT_ID" --quiet 2>/dev/null || true

# Note: Firebase web app config (apiKey, messagingSenderId, appId) is NOT available via API
# These values are only accessible through the Firebase Console
echo -e "${YELLOW}⚠️  Firebase web app config values (apiKey, messagingSenderId, appId)${NC}"
echo -e "${YELLOW}   are NOT available via API - they must be retrieved from Firebase Console${NC}"
echo ""
echo -e "${GREEN}✅ However, we can provide you with direct links!${NC}"
echo ""

echo ""
echo -e "${BLUE}📋 Quick Setup${NC}"
echo -e "${BLUE}=============${NC}"
echo ""
echo -e "${GREEN}Direct links to get Firebase config:${NC}"
echo ""
echo "1. Firebase Console (Project Settings):"
echo "   ${BLUE}https://console.firebase.google.com/project/$PROJECT_ID/settings/general${NC}"
echo ""
echo "2. If no web app exists, create one here:"
echo "   ${BLUE}https://console.firebase.google.com/project/$PROJECT_ID/settings/general/web${NC}"
echo ""
echo "3. Once you have the config, you can:"
echo ""
echo "   ${YELLOW}Option A: Export as environment variables${NC}"
echo "   export FIREBASE_API_KEY=\"AIza...\""
echo "   export FIREBASE_MESSAGING_SENDER_ID=\"123456789\""
echo "   export FIREBASE_APP_ID=\"1:123456789:web:abc123\""
echo "   make deploy-web-simple PROJECT_ID=\"$PROJECT_ID\""
echo ""
echo "   ${YELLOW}Option B: Create a .env file${NC}"
echo "   Create web/frontend/.env.local with:"
echo "   VITE_FIREBASE_API_KEY=AIza..."
echo "   VITE_FIREBASE_MESSAGING_SENDER_ID=123456789"
echo "   VITE_FIREBASE_APP_ID=1:123456789:web:abc123"
echo ""
echo -e "${GREEN}💡 Tip:${NC} The script will auto-detect these values:"
echo "   - FIREBASE_AUTH_DOMAIN = $PROJECT_ID.firebaseapp.com"
echo "   - FIREBASE_PROJECT_ID = $PROJECT_ID"
echo "   - FIREBASE_STORAGE_BUCKET = $PROJECT_ID.appspot.com"
echo ""
echo -e "${YELLOW}⚠️  You still need to provide:${NC}"
echo "   - FIREBASE_API_KEY (from Firebase Console)"
echo "   - FIREBASE_MESSAGING_SENDER_ID (from Firebase Console)"
echo "   - FIREBASE_APP_ID (from Firebase Console)"
echo ""
echo -e "${BLUE}🔗 Open Firebase Console now?${NC}"
echo "   (This will open the project settings page in your browser)"
read -p "   Open browser? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open &> /dev/null; then
        open "https://console.firebase.google.com/project/$PROJECT_ID/settings/general"
        echo -e "${GREEN}✅ Opened Firebase Console in browser${NC}"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "https://console.firebase.google.com/project/$PROJECT_ID/settings/general"
        echo -e "${GREEN}✅ Opened Firebase Console in browser${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not open browser automatically${NC}"
        echo -e "${YELLOW}   Please visit: https://console.firebase.google.com/project/$PROJECT_ID/settings/general${NC}"
    fi
fi
echo ""

