# Agent Directory - Simple Test Agent

## Overview

This directory contains a simple test agent implementation demonstrating basic Google ADK concepts, specifically how to create an agent with a custom tool function.

## Implementation Summary

### Files

- **`agent.py`**: Defines the root agent with a custom arithmetic tool
- **`tools.py`**: Contains the `test_agent` function that squares a number
- **`main.py`**: Simple test script to verify the tool works independently
- **`__init__.py`**: Package initialization

### Code Structure

#### `agent.py`

Creates a basic agent using Google ADK with:
- **Model**: `gemini-2.0-flash`
- **Name**: `test_agent_v1`
- **Purpose**: Arithmetic operations through function calling
- **Tool**: Single custom tool (`test_agent`) for squaring numbers

Key implementation details:
```python
from google.adk.agents import Agent
from .tools import test_agent

root_agent = Agent(
    name="test_agent_v1",
    model="gemini-2.0-flash",
    description="Testing the agent.",
    instruction="You are a helpful arithmetic agent...",
    tools=[test_agent],  # Pass function directly
)
```

#### `tools.py`

Implements a simple tool function:
- **Function**: `test_agent(n1: str)`
- **Purpose**: Squares a number (converts string to float, then squares)
- **Returns**: Float result

This demonstrates how any Python function can be used as an agent tool - the ADK automatically converts it to a tool the LLM can call.

### Usage

#### Direct Tool Testing

```bash
python agent/main.py
```

This tests the tool function directly without the agent.

#### Agent Integration

To use this agent in a runner (similar to `main.py` in the root):

```python
from agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Create session and runner
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="test_app",
    session_service=session_service,
)
```

## Key Concepts Demonstrated

1. **Agent Creation**: Basic agent instantiation with model, description, and instructions
2. **Custom Tools**: How to define and pass Python functions as tools
3. **Tool Function Design**: Functions are automatically converted to tools based on:
   - Function signature (parameter names become tool parameters)
   - Docstrings (become tool descriptions)
   - Type hints (help define parameter types)

## Example Queries

Once integrated with a runner, users can ask:
- "What is 5 squared?"
- "Calculate the square of 12"
- "Use test_agent to find 8 squared"

The agent will:
1. Recognize the need to use the `test_agent` tool
2. Extract the number from the query
3. Call the tool function
4. Return the squared result

## Differences from Other Agents

- **Simplest implementation**: No external service dependencies
- **Single custom tool**: Demonstrates minimal tool integration
- **Synchronous**: No async patterns (though agents can be used with async runners)
- **Pure function tool**: Tool has no side effects

## Learning Objectives

This directory teaches:
- Basic agent structure
- Custom tool definition
- Function-to-tool conversion
- Simple agent-testing patterns
