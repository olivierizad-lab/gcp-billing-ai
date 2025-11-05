#!/bin/bash
# Check logs for Agent Engine errors

PROJECT_ID="qwiklabs-asl-04-8e9f23e85ced"
REASONING_ENGINE_ID="${1:-6641107406371684352}"

echo "Checking logs for Reasoning Engine ID: $REASONING_ENGINE_ID"
echo "Project: $PROJECT_ID"
echo ""
echo "Recent ERROR and WARNING logs:"
echo "=============================="
gcloud logging read "resource.labels.reasoning_engine_id=$REASONING_ENGINE_ID AND severity>=WARNING" \
  --project=$PROJECT_ID \
  --limit=20 \
  --format="table(timestamp,severity,textPayload,jsonPayload.message)" \
  2>&1

echo ""
echo "Recent logs (last 30):"
echo "======================"
gcloud logging read "resource.labels.reasoning_engine_id=$REASONING_ENGINE_ID" \
  --project=$PROJECT_ID \
  --limit=30 \
  --format="value(timestamp,severity,textPayload)" \
  2>&1 | head -50
