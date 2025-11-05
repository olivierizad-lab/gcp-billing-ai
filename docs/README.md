# GCP Billing AI - Complete Documentation

This directory contains comprehensive documentation for all components of the GCP Billing AI project.

## 📚 Documentation Index

### Agent Implementations

- **[bq_agent_mick](./agents/bq_agent_mick.md)** - Alternative BigQuery agent implementation
  - Async/await patterns
  - Environment variable configuration
  - Explicit credential handling
  - Agent Engine deployment ready

- **[bq_agent](./agents/bq_agent.md)** - Production-ready BigQuery agent
  - Synchronous agent creation
  - Explicit tool configuration
  - Write mode blocking for security
  - Hardcoded table references

- **[agent](./agents/agent.md)** - Simple test agent
  - Basic arithmetic operations
  - Custom tool demonstration
  - Learning example

- **[asl_agent](./agents/asl_agent.md)** - Mock time tool example
  - Structured tool returns
  - Type hints demonstration
  - Mock data patterns

### Deployment Guides

- **[bq_agent_mick Deployment](./agents/bq_agent_mick_deployment.md)** - Complete deployment guide for bq_agent_mick
  - Agent Engine deployment
  - Cloud Run deployment
  - Configuration options

- **[bq_agent_mick Usage](./agents/bq_agent_mick_usage.md)** - Usage guide for deployed agents
  - Querying deployed agents
  - API examples
  - Troubleshooting

### Testing

- **[Test Documentation](./tests/tests.md)** - Testing strategies and examples
  - Unit testing
  - Integration testing
  - Agent validation

## 🚀 Quick Reference

### Deployment Commands

```bash
# Deploy individual agents
make deploy-bq-agent-mick
make deploy-bq-agent

# Deploy all agents
make deploy-all-agents

# Deploy specific agent with custom settings
make deploy-agent-engine AGENT_DIR=bq_agent_mick AGENT_NAME=custom_name
```

### Project Structure

```
gcp-billing-ai/
├── agent/              # Simple test agent
├── asl_agent/          # Mock time tool example
├── bq_agent/           # Production-ready BigQuery agent
├── bq_agent_mick/      # Alternative BigQuery agent
├── scripts/            # Shared deployment scripts
├── docs/               # Documentation (this folder)
├── tests/              # Test files
└── Makefile           # Build automation
```

## 🔧 Common Tasks

### Setting Up Development Environment

```bash
# 1. Clone the repository
git clone <repo-url>
cd gcp-billing-ai

# 2. Set up Python virtual environment
make setup

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Set GCP project
export PROJECT_ID=your-project-id
```

### Deploying to Vertex AI Agent Engine

```bash
# Check prerequisites
make check-prereqs

# Deploy an agent
make deploy-bq-agent-mick

# Update REASONING_ENGINE_ID after deployment
# Edit bq_agent_mick/.env or query script
```

### Querying Deployed Agents

```bash
# Using the query module
python -m bq_agent_mick.query_agent "What are the total costs by top 10 services?"

# Or use the test script
python bq_agent_mick/test_agent.py "Your question here"
```

## 📖 Key Concepts

### Agent Development Kit (ADK)

The Google ADK provides:
- **Agents**: LLM-powered agents with capabilities and instructions
- **Tools**: Functions agents can call (BigQuery toolsets, custom tools)
- **Sessions**: Conversation state management
- **Runners**: Execution engine with async event streaming
- **Security**: Write mode blocking for production safety

### BigQuery Integration

Both agents use:
- `BigQueryToolset` - ADK-provided tools for BigQuery
- `WriteMode.BLOCKED` - Security configuration
- Application Default Credentials (ADC) - Authentication

### Deployment Options

1. **Vertex AI Agent Engine** (Recommended)
   - Fully managed
   - Automatic scaling
   - Built-in monitoring

2. **Cloud Run**
   - Containerized deployment
   - Custom service configuration
   - Manual scaling

## 🔍 Troubleshooting

### Common Issues

1. **Deployment fails with "App name mismatch"**
   - Ensure `agent_engine_app.py` exists and has explicit `app_name`
   - See agent-specific deployment docs

2. **Agent not returning query results**
   - Check BigQuery permissions
   - Verify `REASONING_ENGINE_ID` is correct
   - Check Cloud Logs for errors

3. **Module not found errors**
   - Ensure virtual environment is activated
   - Run `make setup` to install dependencies

For more detailed troubleshooting, see the agent-specific documentation.

## 📝 Additional Resources

- [Google ADK Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/agent/overview)
- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)

## 🤝 Contributing

When adding new agents or features:
1. Create agent directory with `agent.py` and `__init__.py`
2. Add `agent_engine_app.py` for Agent Engine deployment
3. Add documentation to `docs/agents/`
4. Update `Makefile` with deployment targets
5. Test deployment and querying

## 📄 License

Copyright 2025 Google LLC

Licensed under the Apache License, Version 2.0
