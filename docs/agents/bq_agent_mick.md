# BQ Agent Mick Directory - Alternative BigQuery Agent Implementation

## Overview

This directory contains an alternative implementation of a BigQuery agent using async/await patterns and environment variable configuration. It demonstrates a different approach to agent initialization compared to the `bq_agent/` directory.

## Implementation Summary

### Files

- **`agent.py`**: Defines the BigQuery agent with async initialization pattern
- **`__init__.py`**: Package initialization

### Code Structure

#### `agent.py`

Key features:

**Environment Configuration**:
```python
PROJECT_ID = os.environ.get("BQ_PROJECT", "qwiklabs-asl-04-8e9f23e85ced")
DATASET = os.environ.get("BQ_DATASET", "qwiklabs-asl-04-8e9f23e85ced.gcp_billing_data")
LOCATION = os.environ.get("BQ_LOCATION", "US")
```

**Explicit Credentials**:
```python
credentials, _ = google.auth.default()
bq_tools = BigQueryToolset(
    credentials_config=BigQueryCredentialsConfig(credentials=credentials)
)
```

**Async Agent Building**:
```python
async def _build_root_agent():
    tools = await bq_tools.get_tools()  # Async tool retrieval
    # Filter to only BigQuery tools
    tools = [t for t in tools if "bigquery" in getattr(t, "name", "").lower()]
    return Agent(
        name="bq_agent",
        model="gemini-2.5-flash",
        description="Answers questions by inspecting BigQuery metadata and running SQL.",
        instruction=(f"Project: {PROJECT_ID} (location {LOCATION}). Prefer dataset {DATASET}."),
        tools=tools,
    )
```

**Sync Wrapper**:
```python
def _build_root_agent_sync():
    import asyncio
    try:
        import nest_asyncio
        nest_asyncio.apply()  # Allows nested event loops
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_build_root_agent())
    except RuntimeError:
        return asyncio.run(_build_root_agent())

root_agent = _build_root_agent_sync()
```

## Key Differences from bq_agent/

### 1. Async Tool Retrieval

This implementation explicitly retrieves tools asynchronously:
```python
tools = await bq_tools.get_tools()
```

This is necessary when tools require async initialization or when you want to filter/process tools before agent creation.

### 2. Tool Filtering

The implementation filters tools to only include BigQuery tools:
```python
tools = [t for t in tools if "bigquery" in getattr(t, "name", "").lower()]
```

This is a defensive pattern to ensure only intended tools are included.

### 3. Environment Variable Configuration

Uses environment variables with defaults:
- More flexible than hardcoded values
- Allows configuration without code changes
- Supports multiple environments (dev, staging, prod)

### 4. Explicit Credential Handling

Explicitly retrieves and passes credentials:
```python
credentials, _ = google.auth.default()
```

More explicit than relying on implicit ADC.

### 5. Dynamic Instructions

Instructions built dynamically from environment variables:
```python
instruction=(f"Project: {PROJECT_ID} (location {LOCATION}). Prefer dataset {DATASET}.")
```

### 6. Sync Wrapper Pattern

Uses `nest_asyncio` to handle async code in sync contexts:
- Allows async agent building in synchronous scripts
- Useful when called from CLI or sync entry points
- Falls back to `asyncio.run()` if nest_asyncio unavailable

### 7. Newer Model

Uses `gemini-2.5-flash` instead of `gemini-2.0-flash`.

## Usage

### Environment Setup

Set environment variables:
```bash
export BQ_PROJECT="your-project-id"
export BQ_DATASET="project.dataset"
export BQ_LOCATION="US"
```

### Using the Agent

```python
from bq_agent_mick.agent import root_agent

# Agent is ready to use (already initialized)
runner = Runner(
    agent=root_agent,
    app_name="bq_app",
    session_service=session_service,
)
```

### Direct Async Usage

If you're already in an async context:

```python
from bq_agent_mick.agent import _build_root_agent

agent = await _build_root_agent()
```

## When to Use This Pattern

This implementation is better suited for:

1. **Dynamic Configuration**: When configuration needs to change based on environment
2. **Tool Filtering**: When you need to filter or modify tools before agent creation
3. **Async-First Designs**: When your application is already async
4. **CLI Tools**: When building command-line tools that need async agent building
5. **Multiple Environments**: When deploying to different environments with different configs

## nest_asyncio

The `nest_asyncio` library is used to allow nested event loops, which is necessary when:
- You need to call async code from sync code
- You're using ADK CLI tools that may already have event loops
- You're in environments like Jupyter notebooks that have existing loops

## Comparison Summary

| Feature | bq_agent/ | bq_agent_mick/ |
|---------|-----------|----------------|
| Agent Creation | Synchronous | Async with sync wrapper |
| Configuration | Hardcoded | Environment variables |
| Tool Handling | Direct toolset | Filtered tools list |
| Credentials | Implicit ADC | Explicit credentials |
| Instructions | Static | Dynamic (from env vars) |
| Model | gemini-2.0-flash | gemini-2.5-flash |
| Use Case | Simple, straightforward | Flexible, configurable |

## Learning Objectives

This directory demonstrates:
- Async/await patterns in agent initialization
- Environment variable configuration patterns
- Tool filtering and processing
- Sync wrappers for async code
- Dynamic instruction generation
- Handling nested event loops

## Production Considerations

For production:
- Validate environment variables
- Handle missing configurations gracefully
- Consider using a config management library
- Document required environment variables
- Add configuration validation at startup

## Deployment

This agent can be deployed for production use in several ways:

1. **Cloud Run Service** (Recommended) - Package as a web service
2. **Vertex AI Agent Builder Console** - Manual configuration
3. **Local Development** - Run directly with `main.py`

See [`DEPLOYMENT_GUIDE.md`](../DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

Quick info:
```bash
# Get deployment options
python bq_agent_mick/deploy_python.py --project YOUR_PROJECT_ID
```

**Note**: ADK doesn't have a direct "deploy to Vertex AI" command. See `DEPLOYMENT_GUIDE.md` for deployment strategies.
