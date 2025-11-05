# Session Management for Vertex AI Reasoning Engines

## Overview

Vertex AI Reasoning Engines manage sessions internally to maintain conversation context and state. These sessions are created automatically when you query a deployed Reasoning Engine.

## Why Can't I Delete a Deployment?

When you try to delete a Reasoning Engine deployment, you may encounter this error:

```
HTTP 400: The ReasoningEngine contains child resources: sessions
```

This means the deployment has active sessions that must be terminated before deletion.

## Understanding Sessions

**What are sessions?**
- Sessions maintain conversation context between queries to your agent
- They are created automatically when you send queries to the Reasoning Engine
- Sessions help the agent remember previous interactions within a conversation

**Session lifecycle:**
- Created: When you first query a Reasoning Engine (via `query()` or `stream_query()`)
- Active: While being used for queries
- Expired: After a period of inactivity (typically 30-60 minutes, but varies)

## How to Handle Active Sessions

### Option 1: Wait for Sessions to Expire (Recommended)

Sessions automatically expire after a period of inactivity (usually 30-60 minutes). Simply wait and try deleting again later.

```bash
# Try cleanup now
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1

# If it fails due to sessions, wait 30-60 minutes and try again
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1
```

### Option 2: Delete via Google Cloud Console

1. Go to [Vertex AI Agent Engine Console](https://console.cloud.google.com/vertex-ai/agents/agent-engines)
2. Select your project and region
3. Find the deployment you want to delete
4. Click on the deployment name
5. Look for session management options or delete button
6. Delete the deployment

The Console may provide additional options for managing sessions that aren't available via API.

### Option 3: Manual API Retry

Use the cleanup script's manual retry approach:

```bash
# First attempt (may fail due to sessions)
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1

# Wait 30-60 minutes, then retry
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1
```

### Option 4: Explore Session Management (Experimental)

We've created a utility script to explore session management options:

```bash
# List and explore available session endpoints
python scripts/manage_sessions.py --engine-id <REASONING_ENGINE_ID> --list

# Attempt to force delete (will still fail if sessions are active)
python scripts/manage_sessions.py --engine-id <REASONING_ENGINE_ID> --force-delete
```

**Note:** Currently, Vertex AI Reasoning Engines don't expose a public API to directly list or terminate sessions. This is by design for security and session management reasons.

## Why No Direct Session Management API?

Vertex AI manages sessions internally for several reasons:

1. **Security**: Prevents unauthorized access to session data
2. **State Management**: Ensures proper cleanup and resource management
3. **Performance**: Allows for optimized session handling
4. **Abstraction**: Sessions are an implementation detail of the Reasoning Engine

## Best Practices

1. **Plan deployments**: Avoid creating many deployments during development
   - Use `make cleanup-deployments` regularly to clean up old deployments
   - Consider keeping only 1-2 active deployments per agent

2. **Wait for inactivity**: Before deleting a deployment, ensure no active queries are running
   - Wait a few minutes after your last query
   - Then attempt deletion

3. **Monitor deployments**: Use `make list-deployments` to see all your deployments
   ```bash
   make list-deployments AGENT_NAME=bq_agent_mick
   ```

4. **Use the Console**: For urgent deletions, the Google Cloud Console may have additional options

## Related Scripts

- `scripts/cleanup_old_deployments.py` - Clean up old deployments
- `scripts/list_agent_engines.py` - List all deployments
- `scripts/manage_sessions.py` - Explore session management (experimental)

## Troubleshooting

**Q: My deployment still can't be deleted after waiting hours.**

A: Try:
1. Check if you're still making queries to that deployment
2. Delete via the Google Cloud Console (may have force-delete options)
3. Contact Google Cloud Support if the issue persists

**Q: Can I prevent sessions from being created?**

A: Sessions are created automatically when you query the Reasoning Engine. This is required for proper agent functionality and cannot be disabled.

**Q: How long do sessions last?**

A: Sessions typically expire after 30-60 minutes of inactivity, but this may vary. The exact timeout is managed internally by Vertex AI.
