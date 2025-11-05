# Using bq_agent_mick Agent Engine

Your BigQuery agent is successfully deployed to Vertex AI Agent Engine! 🎉

> **Note**: If you've updated the agent code (especially instructions), you'll need to redeploy:
> ```bash
> make deploy-agent-engine
> ```
> 
> **Important**: After redeployment, update the `REASONING_ENGINE_ID` in `test_agent.py` with the new ID from the deployment output, or set it via environment variable:
> ```bash
> export REASONING_ENGINE_ID="your-new-id"
> ```

## Current Status

✅ **Deployed**: Agent is live and running  
✅ **API Endpoints Found**: `:query` and `:streamQuery?alt=sse`  
✅ **Working Format**: Successfully tested with `streamQuery` endpoint!

## Agent Engine Information

- **Agent Name**: `bq_agent_mick`
- **Project**: `qwiklabs-asl-04-8e9f23e85ced`
- **Location**: `us-central1`
- **Reasoning Engine ID**: `6060143054440890368`
- **Console**: https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=qwiklabs-asl-04-8e9f23e85ced

## How to Query Your Agent

### Option 1: Use the Test Script (Easiest!) ✅

The `test_agent.py` script is now working:

```bash
# Single query
python bq_agent_mick/test_agent.py "What are the top 10 services by cost?"

# Interactive mode
python bq_agent_mick/test_agent.py
```

### Option 2: Use Python Code Directly

```python
from google.auth import default
from google.auth.transport.requests import Request
import requests
import json

# Authenticate
credentials, _ = default()
if not credentials.valid:
    credentials.refresh(Request())

# Configuration
PROJECT_ID = "qwiklabs-asl-04-8e9f23e85ced"
LOCATION = "us-central1"
REASONING_ENGINE_ID = "6060143054440890368"

# Query endpoint (streaming - recommended)
stream_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}:streamQuery?alt=sse"

headers = {
    "Authorization": f"Bearer {credentials.token}",
    "Content-Type": "application/json",
}

payload = {
    "input": {
        "message": "What are the top 10 services by cost?",
        "user_id": "test_user",
        "session_id": "test_session"
    }
}

# Send request and read SSE stream
response = requests.post(stream_url, headers=headers, json=payload, stream=True, timeout=120)

if response.status_code == 200:
    for line in response.iter_lines(decode_unicode=True):
        if line and line.startswith("data: "):
            data = json.loads(line[6:])
            print(data)  # Process each streaming chunk
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Option 3: Use cURL

```bash
# Get access token
ACCESS_TOKEN=$(gcloud auth print-access-token)

# Query the agent
curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/qwiklabs-asl-04-8e9f23e85ced/locations/us-central1/reasoningEngines/6060143054440890368:streamQuery?alt=sse" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "message": "What are the top 10 services by cost?",
      "user_id": "test_user",
      "session_id": "test_session"
    }
  }'
```

## API Details

### Endpoints

1. **Stream Query** (Recommended - Real-time streaming):
   ```
   POST https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{ID}:streamQuery?alt=sse
   ```
   - Returns: Server-Sent Events (SSE) stream
   - Best for: Interactive queries with real-time responses

2. **Query** (Alternative - Single response):
   ```
   POST https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{ID}:query
   ```
   - Returns: Single JSON response
   - Note: Requires agent to have a default `query` method (currently uses `stream_query`)

### Request Format

```json
{
  "input": {
    "message": "Your question here",
    "user_id": "user_id_string",
    "session_id": "session_id_string"
  }
}
```

### Response Format (StreamQuery)

Server-Sent Events (SSE) format:
```
data: {"content": "response text chunk 1"}
data: {"content": "response text chunk 2"}
...
```

## Troubleshooting

**Common Issues**:

1. **Empty Stream Response**:
   - The agent may take 30-60 seconds to process complex queries
   - Be patient and wait for the stream to start
   - Check agent logs in the Console if no response after 2 minutes

2. **Authentication Errors**:
   ```bash
   gcloud auth application-default login
   ```

3. **Timeout Errors**:
   - Increase timeout to 120 seconds for complex queries
   - The streamQuery endpoint can take time to start returning data

4. **400 Errors**:
   - Ensure payload uses `{"input": {...}}` structure
   - Include `message`, `user_id`, and `session_id` in the input object

## Alternative: Use Locally

While we figure out the Agent Engine API, you can always test the agent locally:

```bash
python main.py
```

This uses the same agent code, just running locally instead of in Agent Engine.

## Help Us Improve

If you discover the correct API format, please share it so we can update the scripts!
