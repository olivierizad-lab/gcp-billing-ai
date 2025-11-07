# GCP Billing AI - Google ADK Agent Solutions

> 📚 **📖 [View Full Documentation](https://olivierizad-lab.github.io/gcp-billing-ai/)** - Complete documentation with architecture, deployment guides, and more

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

**Option 1: Web Interface** 🎨

Start the React web interface for interacting with your agents:
```bash
# Start backend (Terminal 1)
cd web/backend
pip install -r requirements.txt
python main.py

# Start frontend (Terminal 2)
cd web/frontend
npm install
npm run dev
```

Then open http://localhost:3000 in your browser!

See [docs/START_HERE.md](./docs/START_HERE.md) for quick setup.

**Option 2: Command Line**

```bash
# For bq_agent_mick
python -m bq_agent_mick.query_agent "What are the total costs by top 10 services?"

# For bq_agent
python -m bq_agent.query_agent "What are the total costs by top 10 services?"

# Interactive mode
python -m bq_agent_mick.interactive
```

## Available Agents

- **`bq_agent_mick`** - Alternative BigQuery agent implementation with async patterns and environment variable configuration
- **`bq_agent`** - Production-ready BigQuery agent with explicit tool configuration and write blocking

## Web Interface

🎨 **GCP Billing Agent Web Interface**

A modern web interface for interacting with your deployed Vertex AI Agent Engine agents. Features:
- Real-time streaming responses
- Multi-agent support
- Clean, modern UI
- Easy agent switching
- Firestore authentication
- Query history management

👉 **[Get Started with the Web Interface](./docs/START_HERE.md)** - Quick setup guide

## Documentation

📚 **Full documentation is available in the [`docs/`](./docs/) folder:**

- **[Architecture](./docs/architecture.md)** - Complete system architecture with Mermaid diagrams
- **[Getting Started](./docs/START_HERE.md)** - Quick start guide
- **[Deployment Guide](./docs/AUTOMATED_DEPLOYMENT.md)** - Automated deployment instructions
- **[Authentication](./docs/AUTHENTICATION_SETUP.md)** - Firestore authentication setup
- **[Agent Documentation](./docs/agents/)**:
  - [bq_agent_mick](./docs/agents/bq_agent_mick.md) - Alternative implementation details
  - [bq_agent](./docs/agents/bq_agent.md) - Production-ready agent details
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
