#!/bin/bash
# Script to create a GitHub release from a tag

set -e

TAG=$1
if [ -z "$TAG" ]; then
    echo "Usage: $0 <tag>"
    echo "Example: $0 v1.3.0-rc2"
    exit 1
fi

# Check if tag exists
if ! git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "Error: Tag $TAG does not exist"
    exit 1
fi

# Get tag message
TAG_MESSAGE=$(git tag -n9 "$TAG" | tail -n +2)

# Create release notes from CHANGELOG.md
CHANGELOG_SECTION=$(sed -n "/\[$TAG\]/,/^## /p" CHANGELOG.md | head -n -1 || sed -n "/\[$TAG\]/,\$p" CHANGELOG.md)

if [ -z "$CHANGELOG_SECTION" ]; then
    # Fallback to tag message
    RELEASE_NOTES="$TAG_MESSAGE"
else
    RELEASE_NOTES="$CHANGELOG_SECTION"
fi

echo "Creating release for $TAG..."
echo "Release notes:"
echo "$RELEASE_NOTES"
echo ""

# Create release using GitHub CLI
if command -v gh &> /dev/null; then
    gh release create "$TAG" \
        --title "$TAG" \
        --notes "$RELEASE_NOTES" \
        --repo olivierizad-lab/gcp-billing-ai
    echo "✅ Release created successfully!"
else
    echo "⚠️  GitHub CLI (gh) not found. Install it from: https://cli.github.com/"
    echo ""
    echo "Or create the release manually at:"
    echo "https://github.com/olivierizad-lab/gcp-billing-ai/releases/new?tag=$TAG"
    echo ""
    echo "Release notes to paste:"
    echo "---"
    echo "$RELEASE_NOTES"
    echo "---"
fi

