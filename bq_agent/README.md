# BQ Agent Directory - BigQuery Agent for Billing Analysis

## Overview

This directory contains a production-ready BigQuery agent implementation designed to answer questions about GCP billing data. It uses the ADK's built-in BigQuery toolset to automatically generate and execute SQL queries based on natural language questions.

## Implementation Summary

### Files

- **`agent.py`**: Defines the BigQuery agent with toolset configuration
- **`tools.py`**: Contains a test tool (unrelated to BigQuery functionality)
- **`__init__.py`**: Package initialization

### Code Structure

#### `agent.py`

Main agent implementation with:

**Configuration**:
- **Model**: `gemini-2.0-flash`
- **Name**: `bigquery_agent`
- **Security**: Write operations blocked via `WriteMode.BLOCKED`
- **Credentials**: Uses Application Default Credentials (ADC)

**BigQuery Toolset**:
```python
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
bigquery_toolset = BigQueryToolset(
    bigquery_tool_config=tool_config
)
```

**Agent Definition**:
```python
root_agent = Agent(
    model=GEMINI_MODEL,
    name=AGENT_NAME,
    description="Agent to answer questions about BigQuery data...",
    instruction="""
        You are a data science agent with access to several BigQuery tools.
        Be an assistant that will automatically map the questions to a query.
        All data is in this table: qwiklabs-asl-04-8e9f23e85ced.billing_dataset.fake_billing_data
        You should always call get_table_info to retrieve the schema from this table.
    """,
    tools=[bigquery_toolset],
)
```

### Security Configuration

The agent is configured with `WriteMode.BLOCKED`, meaning:
- ✅ Can execute SELECT queries (read operations)
- ✅ Can inspect table schemas and metadata
- ❌ Cannot INSERT, UPDATE, DELETE, or modify data
- ❌ Cannot create/drop tables or datasets

This is a critical security feature for production use.

### BigQuery Toolset Capabilities

The `BigQueryToolset` provides the agent with tools for:

1. **`get_table_info`**: Retrieve schema and metadata for tables
2. **`execute_query`**: Run SQL SELECT queries
3. **`list_datasets`**: Discover available datasets
4. **`list_tables`**: List tables in a dataset
5. **`get_dataset_info`**: Get dataset metadata

The agent automatically chooses which tools to use based on the user's question.

## Usage

This is the main agent used in the root `main.py`:

```python
import bq_agent.agent as agent

# Agent is already configured and ready to use
runner = Runner(
    agent=agent.root_agent,
    app_name="agents",
    session_service=session_service,
)
```

### Example Queries

The agent can handle queries like:

- "Could you give me the top 10 services by highest cost spendings?"
- "What are the projects with highest month to month cost spendings for September to October 2025?"
- "Show me the total cost per TLA for invoice month 202510"
- "What's the schema of the billing data table?"

### Agent Workflow

For each query, the agent typically:

1. **Understands the intent**: Parses the natural language question
2. **Retrieves schema**: Calls `get_table_info` to understand table structure
3. **Generates SQL**: Creates appropriate SQL query based on schema and question
4. **Executes query**: Uses `execute_query` to run the SQL
5. **Formats results**: Presents results in a readable format (often tabular)

## Key Implementation Details

### Instruction Design

The agent instructions are carefully crafted to:
- Guide the agent to use BigQuery tools
- Specify the target table explicitly
- Encourage schema inspection before querying
- Map questions to SQL automatically

### Credentials

Uses Application Default Credentials, which means:
- Works with `gcloud auth application-default login`
- Works in GCP environments (Cloud Run, GCE, etc.)
- Can use service account credentials
- Decoupled from agent lifecycle

### Table Reference

The agent is hardcoded to work with:
- **Project**: `qwiklabs-asl-04-8e9f23e85ced`
- **Dataset**: `billing_dataset`
- **Table**: `fake_billing_data`

This can be modified in the instruction string.

## Integration with Root

The root `main.py` uses this agent and demonstrates:

1. **Session Management**: Creates sessions for conversation state
2. **Async Execution**: Uses `runner.run_async()` for async event streaming
3. **Event Handling**: Processes events to extract final responses
4. **Error Handling**: Handles escalations and errors gracefully

## Comparison with bq_agent_mick

Differences from the alternative implementation:

- **Synchronous agent creation**: Agent created directly (no async wrapper)
- **Explicit tool config**: Write mode blocking configured explicitly
- **Hardcoded table**: Table reference in instructions
- **Simpler structure**: More straightforward for learning

## Learning Objectives

This directory teaches:
- Production-ready agent configuration
- Security best practices (write blocking)
- BigQuery toolset integration
- Instruction engineering for data agents
- Schema-first querying patterns

## Production Considerations

For production use, consider:
- Making table references configurable via environment variables
- Adding query result caching
- Implementing query cost limits
- Adding query validation before execution
- Monitoring and logging query patterns
- Rate limiting for user queries
