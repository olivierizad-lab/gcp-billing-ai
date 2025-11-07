#!/bin/bash
# Script to configure GitHub Pages to use GitHub Actions
# Requires GitHub CLI (gh) to be installed and authenticated

set -e

REPO="olivierizad-lab/gcp-billing-ai"

echo "Checking GitHub Pages configuration for $REPO..."

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo ""
    echo "Install it from: https://cli.github.com/"
    echo ""
    echo "Or configure manually:"
    echo "1. Go to: https://github.com/$REPO/settings/pages"
    echo "2. Under 'Source', select 'GitHub Actions'"
    echo "3. Save the changes"
    exit 1
fi

# Check if authenticated
if ! gh auth status &>/dev/null; then
    echo "❌ GitHub CLI is not authenticated."
    echo "Run: gh auth login"
    exit 1
fi

# Get current Pages configuration
echo "Current GitHub Pages configuration:"
gh api "/repos/$REPO/pages" 2>&1 || echo "Could not fetch Pages config"

echo ""
echo "Note: GitHub Pages source must be changed via the web interface."
echo ""
echo "To configure:"
echo "1. Visit: https://github.com/$REPO/settings/pages"
echo "2. Under 'Source', select 'GitHub Actions' (not 'Deploy from a branch')"
echo "3. Click 'Save'"
echo ""
echo "After changing, your documentation will be served from GitHub Actions builds!"

