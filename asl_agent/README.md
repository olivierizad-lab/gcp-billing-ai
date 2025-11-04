# ASL Agent Directory - Mock Time Tool Example

## Overview

This directory contains a simple agent example demonstrating a mock tool implementation. The agent provides a "get current time" functionality, though it returns mock data rather than real time information.

## Implementation Summary

### Files

- **`agent.py`**: Defines the root agent with a mock time tool
- **`__init__.py`**: Package initialization

### Code Structure

#### `agent.py`

Creates an agent with:
- **Model**: `gemini-2.5-flash`
- **Name**: `root_agent`
- **Purpose**: Tell the "current time" in specified cities (mock implementation)
- **Tool**: `get_current_time(city: str)` function

Key implementation:
```python
from google.adk.agents.llm_agent import Agent

def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="Tells the current time in a specified city.",
    instruction="You are a helpful assistant...",
    tools=[get_current_time],
)
```

### Tool Implementation

The `get_current_time` tool:
- **Takes**: A city name (string parameter)
- **Returns**: A dictionary with status, city, and time
- **Current behavior**: Always returns "10:30 AM" regardless of actual time or city
- **Purpose**: Demonstrates structured return values from tools

## Usage

This agent can be used with any ADK runner:

```python
from asl_agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="time_app",
    session_service=session_service,
)

# Query examples:
# "What time is it in Paris?"
# "Get the current time for New York"
```

## Key Concepts Demonstrated

1. **Structured Tool Returns**: Tools can return dictionaries/structured data
2. **Type Hints**: Using `-> dict` helps the LLM understand return format
3. **Mock Implementations**: Creating tools that simulate real functionality
4. **Tool Documentation**: Docstrings describe tool purpose to the LLM

## Tool Return Format

The tool returns a structured dictionary:
```python
{
    "status": "success",
    "city": "Paris",  # The city requested
    "time": "10:30 AM"  # Mock time value
}
```

This format could be extended to:
- Return actual time based on timezone
- Include date information
- Handle errors with status "error"
- Include timezone information

## Comparison with Other Agents

- **Similar to `agent/`**: Simple custom tool implementation
- **More structured returns**: Returns dict vs simple float in `agent/`
- **Mock data**: Demonstrates placeholder implementation pattern
- **Newer model**: Uses `gemini-2.5-flash` vs `2.0-flash`

## Learning Objectives

This directory demonstrates:
- Structured tool return values
- Mock tool patterns for development
- Agent instruction design for tool usage
- Type hints and documentation importance
