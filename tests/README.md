# Tests Directory - Agent Test Suite

## Overview

This directory contains unit tests for the agent implementations, specifically focusing on testing the BigQuery agent (`bq_agent`). The tests use `pytest` and `unittest` frameworks to verify agent functionality.

## Implementation Summary

### Files

- **`test_agents.py`**: Main test file containing agent test cases

### Code Structure

#### `test_agents.py`

**Test Framework Setup**:
- Uses `unittest.IsolatedAsyncioTestCase` for async test support
- Imports pytest for marking tests
- Sets up ADK services (sessions, artifacts, runners)

**Key Components**:

1. **Test Configuration**:
```python
TEST_AGENT_NAME = "test_agent_name"
TEST_APP_NAME = "test_app_name"
TEST_USER_ID = "test_user_id"
```

2. **Service Initialization**:
```python
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()
```

3. **Test Setup**:
```python
async def asyncSetUp(self):
    self.session = await session_service.create_session(...)
    self.runner = Runner(
        app_name=TEST_APP_NAME,
        agent=bq_agent.agent.root_agent,
        artifact_service=artifact_service,
        session_service=session_service,
    )
```

4. **Helper Method**:
```python
def _run_agent(self, agent, query):
    """Helper method to run an agent and get the final response."""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    events = list(self.runner.run(...))
    # Extract final response from last event
    return final_response
```

### Test Cases

#### Active Tests

**`test_ds_agent_can_be_called_from_root`**:
- Tests the BigQuery agent with a billing query
- Query: "Could you give us the top 3 TLAs with the most cost spendings?"
- Verifies agent produces a non-null response
- Marked with `@pytest.mark.ds_agent`

#### Commented/Inactive Tests

Several test cases are commented out, suggesting future development:

1. **`test_db_agent_can_handle_env_query`**: Database agent test
2. **`test_bqml_agent_can_check_for_models`**: BigQuery ML model checking
3. **`test_bqml_agent_can_execute_code`**: BQML code execution

These reference agents that may not be fully implemented yet.

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test

```bash
pytest tests/test_agents.py::TestAgents::test_ds_agent_can_be_called_from_root
```

### Run with Marker

```bash
pytest -m ds_agent
```

### Run with Verbose Output

```bash
pytest tests/ -v
```

### Run Directly

```bash
python -m pytest tests/
# or
python tests/test_agents.py
```

## Test Structure

### Async Test Pattern

The tests use `IsolatedAsyncioTestCase` which:
- Provides an event loop for async operations
- Isolates each test case
- Allows async setup and teardown methods

### Event Processing

The helper method processes all events from the runner:
```python
events = list(self.runner.run(...))
last_event = events[-1]
final_response = "".join([part.text for part in last_event.content.parts if part.text])
```

This extracts the final text response from the event stream.

## Dependencies

Tests require:
- `pytest`
- `unittest` (standard library)
- ADK packages (`google.adk`, `google.genai`)
- The agent modules being tested

## Test Environment

The tests use:
- **InMemorySessionService**: Ephemeral session storage (not persisted)
- **InMemoryArtifactService**: Temporary artifact storage
- **Test credentials**: Should use test project or mocked BigQuery

## Writing New Tests

### Test Template

```python
@pytest.mark.your_marker
async def test_your_feature(self):
    """Test description."""
    query = "Your test query"
    response = self._run_agent(root_agent, query)
    print(response)  # For debugging
    self.assertIsNotNone(response)
    # Add more assertions as needed
```

### Assertion Patterns

Common assertions:
- `self.assertIsNotNone(response)`: Response exists
- `self.assertIn("expected_text", response)`: Contains specific text
- `self.assertTrue(condition)`: Condition is true
- Custom assertions based on expected JSON structure

## Integration with CI/CD

For continuous integration:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pytest tests/ --junitxml=junit.xml
```

## Mocking Considerations

Current tests use real BigQuery connections. For better isolation, consider:
- Mocking BigQuery client responses
- Using test datasets
- Creating fixtures for common query results
- Using pytest fixtures for agent setup

## Learning Objectives

This directory demonstrates:
- Async test patterns with unittest
- ADK runner testing
- Event stream processing
- Test isolation strategies
- Helper method patterns for reusable test logic

## Future Enhancements

Potential improvements:
- Add more comprehensive test coverage
- Implement mocked BigQuery responses
- Add integration tests for all agent types
- Create test fixtures for common scenarios
- Add performance/load testing
- Test error handling and edge cases
- Validate SQL query generation
