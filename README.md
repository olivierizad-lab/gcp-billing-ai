# GCP Billing AI - Google ADK Agent Solutions

This repository contains multiple BigQuery agent implementations using Google's Agent Development Kit (ADK) for analyzing GCP billing data.

## Quick Start

### Setup

```bash
# Install dependencies
make setup

# Set your GCP project
export PROJECT_ID=your-project-id
```

### Deploy Agents

Deploy individual agents:
```bash
make deploy-bq-agent-mick  # Deploy bq_agent_mick
make deploy-bq-agent       # Deploy bq_agent
```

Or deploy all agents at once:
```bash
make deploy-all-agents
```

### Query Agents

After deployment, query the agents:
```bash
# For bq_agent_mick
python -m bq_agent_mick.query_agent "What are the total costs by top 10 services?"

# For bq_agent (when query script is available)
python -m bq_agent.query_agent "What are the total costs by top 10 services?"
```

## Available Agents

- **`bq_agent_mick`** - Alternative BigQuery agent implementation with async patterns and environment variable configuration
- **`bq_agent`** - Production-ready BigQuery agent with explicit tool configuration and write blocking

## Documentation

📚 **Full documentation is available in the [`docs/`](./docs/) folder:**

- **[Main Documentation](./docs/README.md)** - Project overview and getting started guide
- **[Agent Documentation](./docs/agents/)**:
  - [bq_agent_mick](./docs/agents/bq_agent_mick.md) - Alternative implementation details
  - [bq_agent](./docs/agents/bq_agent.md) - Production-ready agent details
  - [agent](./docs/agents/agent.md) - Simple test agent
  - [asl_agent](./docs/agents/asl_agent.md) - Mock time tool example
- **[Deployment Guides](./docs/agents/)**:
  - [bq_agent_mick Deployment](./docs/agents/bq_agent_mick_deployment.md)
  - [bq_agent_mick Usage](./docs/agents/bq_agent_mick_usage.md)
- **[Testing](./docs/tests/)**:
  - [Test Documentation](./docs/tests/tests.md)

## Makefile Commands

Run `make help` to see all available commands:

```bash
make help                    # Show all available commands
make deploy-bq-agent-mick    # Deploy bq_agent_mick
make deploy-bq-agent         # Deploy bq_agent
make deploy-all-agents       # Deploy all agents
make setup                   # Set up development environment
make check-prereqs          # Check prerequisites
```

## Technologies

- **Google ADK** (`google-adk==1.17.0`) - Agent Development Kit
- **Google GenAI** (`google-genai==1.47.0`) - Gemini model integration
- **BigQuery Client** (`google-cloud-bigquery==3.38.0`) - Direct BigQuery API
- **Vertex AI Agent Engine** - Hosted agent deployment platform

## License

Copyright 2025 Google LLC

Licensed under the Apache License, Version 2.0
