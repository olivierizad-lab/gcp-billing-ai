#!/bin/bash
# Grant BigQuery permissions to Agent Engine service accounts

set -e

PROJECT_ID="qwiklabs-asl-04-8e9f23e85ced"
DATASET="gcp_billing_data"

# Get project number
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null)

if [ -z "$PROJECT_NUMBER" ]; then
    echo "Error: Could not get project number for $PROJECT_ID"
    exit 1
fi

echo "Project: $PROJECT_ID"
echo "Project Number: $PROJECT_NUMBER"
echo ""

# Agent Engine service accounts
AI_PLATFORM_SA="service-$PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com"
COMPUTE_SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

echo "Granting BigQuery permissions to Agent Engine service accounts..."
echo ""

# Grant permissions to AI Platform service account
echo "1. Granting permissions to: $AI_PLATFORM_SA"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$AI_PLATFORM_SA" \
    --role="roles/bigquery.dataViewer" \
    --condition=None 2>/dev/null || echo "  (May already have dataViewer)"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$AI_PLATFORM_SA" \
    --role="roles/bigquery.jobUser" \
    --condition=None 2>/dev/null || echo "  (May already have jobUser)"

# Grant dataset-level permissions
echo "2. Granting dataset-level permissions..."
bq add-iam-policy-binding "$PROJECT_ID:$DATASET" \
    --member="serviceAccount:$AI_PLATFORM_SA" \
    --role="roles/bigquery.dataViewer" 2>/dev/null || echo "  (May already have dataset permissions)"

# Grant permissions to Compute service account (used by some Vertex AI services)
echo "3. Granting permissions to: $COMPUTE_SA"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/bigquery.dataViewer" \
    --condition=None 2>/dev/null || echo "  (May already have dataViewer)"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/bigquery.jobUser" \
    --condition=None 2>/dev/null || echo "  (May already have jobUser)"

bq add-iam-policy-binding "$PROJECT_ID:$DATASET" \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/bigquery.dataViewer" 2>/dev/null || echo "  (May already have dataset permissions)"

echo ""
echo "✓ Permissions granted!"
echo ""
echo "Service accounts with BigQuery access:"
echo "  - $AI_PLATFORM_SA"
echo "  - $COMPUTE_SA"
echo ""
echo "Granted roles:"
echo "  - roles/bigquery.dataViewer (read data)"
echo "  - roles/bigquery.jobUser (run queries)"
