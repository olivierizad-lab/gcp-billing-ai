# billing-ai
This project generates fake billing data and a Gemini Agent to dynamically create some analysis through prompts

## Project Overview

This repository contains learning experiments with Google's Agent Development Kit (ADK), exploring how to build AI agents that interact with BigQuery to analyze GCP billing data through natural language queries. The project demonstrates various agent implementation patterns, from simple custom tools to production-ready BigQuery agents with security configurations.

## Project Structure

```
├── agent/              # Simple test agent with custom arithmetic tool
├── asl_agent/          # Basic agent example with mock time tool  
├── bq_agent/           # Production BigQuery agent for billing analysis
├── bq_agent_mick/      # Alternative BigQuery agent with async patterns
├── tests/              # Unit tests for agents
├── main.py             # Main entry point for running the BigQuery agent
├── constants.py        # Project constants (GCP services, table schemas)
├── create_bigquery_environment.py  # Script to create BigQuery dataset/table
└── generate_fake_data.py           # Script to generate synthetic billing data
```

## Key Components

### Root Files

- **`main.py`**: Main entry point that loads the `bq_agent`, manages sessions, and executes natural language queries against BigQuery billing data. Demonstrates async agent execution and event handling.

- **`constants.py`**: Contains project constants including:
  - GCP service list (50+ services)
  - BigQuery project, dataset, and table names
  - Table schema definitions for billing data (tla, project_id, environment, service_description, invoice_month, usage times, cost)

- **`create_bigquery_environment.py`**: Utility script to create the BigQuery dataset and table structure needed for billing data storage.

- **`generate_fake_data.py`**: Generates synthetic GCP billing data with realistic distributions across projects, services, and time periods. Creates 365 days of billing records using statistical distributions for cost allocation.

### Agent Implementations

Each directory contains a different agent implementation exploring various aspects of Google ADK:

1. **`agent/`** - Simple test agent demonstrating basic tool integration
   - Custom `test_agent` tool that squares numbers
   - Uses `gemini-2.0-flash` model
   - Minimal implementation for learning fundamentals

2. **`asl_agent/`** - Mock agent example with custom tool
   - `get_current_time` tool returning structured data
   - Uses `gemini-2.5-flash` model
   - Demonstrates structured tool returns

3. **`bq_agent/`** - Production-ready BigQuery agent (used by main.py)
   - Uses BigQuery toolset with write operations blocked
   - Configured for billing dataset analysis
   - Security-focused with `WriteMode.BLOCKED`

4. **`bq_agent_mick/`** - Alternative BigQuery agent implementation
   - Async/await patterns with sync wrapper
   - Environment variable configuration
   - Tool filtering and dynamic instructions

5. **`tests/`** - Unit test suite
   - Tests BigQuery agent functionality
   - Uses pytest and unittest frameworks
   - Async test patterns

See each directory's README.md for detailed documentation and implementation summaries.

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Google Cloud credentials**:
   ```bash
   gcloud auth application-default login
   ```

3. **Create BigQuery environment**:
   ```bash
   python create_bigquery_environment.py
   ```

4. **Generate fake billing data** (optional):
   ```bash
   python generate_fake_data.py
   ```

5. **Run the main agent**:
   ```bash
   python main.py
   ```

## Usage Example

The main script demonstrates querying billing data through natural language:

```python
query = "Could you give me the projects with highest month to month cost spendings for the months of september to october of 2025?"
```

The agent will:
1. Parse the natural language query
2. Retrieve table schema information using `get_table_info`
3. Generate appropriate SQL queries
4. Execute queries against BigQuery
5. Format and return results in a readable format

## Key Google ADK Concepts Demonstrated

- **Agents**: LLM-powered agents with specific capabilities and instructions
- **Tools**: Functions that agents can call (BigQuery toolsets, custom tools)
- **Sessions**: Conversation state management with `InMemorySessionService`
- **Runners**: Execution engine for agents with async event streaming
- **Events**: Stream processing of agent responses and tool calls
- **Security**: Write mode blocking for production safety
- **Credentials**: Application Default Credentials (ADC) integration

## Technologies Used

- **Google ADK** (`google-adk==1.17.0`): Agent Development Kit for building AI agents
- **Google GenAI** (`google-genai==1.47.0`): Gemini model integration
- **BigQuery Client** (`google-cloud-bigquery==3.38.0`): Direct BigQuery API access
- **BigQuery Toolset**: ADK-provided tools for BigQuery interaction

## Learning Objectives

This project serves as a learning repository for understanding:
- How to structure AI agents with Google ADK
- BigQuery integration patterns with security best practices
- Custom tool development and function-to-tool conversion
- Session and state management
- Async/await patterns in agent execution
- Environment variable configuration patterns
- Testing strategies for AI agents

## Documentation

Each directory contains detailed README files with:
- Code summaries and implementation details
- Usage examples and integration patterns
- Key concepts and learning objectives
- Comparison with other implementations

## Testing

Run tests with:
```bash
pytest tests/
```

## License

Copyright 2025 Google LLC

Licensed under the Apache License, Version 2.0
