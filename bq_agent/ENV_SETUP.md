# bq_agent Environment Setup

## Quick Start

1. **Deploy the agent** (if not already deployed):
   ```bash
   make deploy-bq-agent
   ```

2. **Find the Reasoning Engine ID**:
   ```bash
   make list-deployments AGENT_NAME=bq_agent
   ```
   
   Copy the latest Reasoning Engine ID from the output.

3. **Create `.env` file**:
   ```bash
   cp .env.example .env
   # Then edit .env and set REASONING_ENGINE_ID=your-id
   ```

4. **Test the agent**:
   ```bash
   python -m bq_agent.query_agent "Show me monthly costs over time"
   ```

## Environment Variables

Create `bq_agent/.env` with:

```bash
# Google Cloud Project Configuration
BQ_PROJECT=qwiklabs-asl-04-8e9f23e85ced
GCP_PROJECT_ID=qwiklabs-asl-04-8e9f23e85ced

# BigQuery Configuration
BQ_DATASET=qwiklabs-asl-04-8e9f23e85ced.gcp_billing_data
BQ_TABLE=billing_data_ndjson
BQ_LOCATION=US

# Vertex AI Agent Engine Configuration
LOCATION=us-central1
REASONING_ENGINE_ID=your-reasoning-engine-id-here
```

## Alternative: Set Environment Variable

Instead of creating `.env`, you can export:

```bash
export REASONING_ENGINE_ID=your-reasoning-engine-id-here
python -m bq_agent.query_agent "Your question"
```
