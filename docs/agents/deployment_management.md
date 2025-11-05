# Agent Engine Deployment Management

## Understanding Agent Engine Deployments

### Why Multiple Deployments Exist

Each time you run `adk deploy agent_engine` or `make deploy-*`, a **new Reasoning Engine instance** is created. The ADK does not update existing deployments; it always creates new ones.

This means:
- ✅ Each deployment is **immutable** (safe, no risk of breaking existing deployments)
- ⚠️ Each deployment creates a **new instance** (can accumulate if not cleaned up)
- 📊 Old deployments remain active unless manually deleted

### Typical Deployment Pattern

During development, you might create many deployments:
1. Initial deployment
2. Fix syntax errors → new deployment
3. Update agent instructions → new deployment
4. Fix configuration issues → new deployment
5. ... and so on

This is **normal** and expected behavior during development.

## Finding the Latest Deployment

### Using the Console

1. Go to [Vertex AI Agent Engine Console](https://console.cloud.google.com/vertex-ai/agents/agent-engines)
2. Sort by "Created" column (newest first)
3. The top entry is your latest deployment
4. Copy the **Reasoning Engine ID** from the Resource name

### Using the Script

List all deployments for a specific agent:

```bash
# List all deployments
make list-deployments

# List only bq_agent_mick deployments
make list-deployments AGENT_NAME=bq_agent_mick

# Or use the script directly
python scripts/list_agent_engines.py --filter-name bq_agent_mick
```

This will show:
- All deployments sorted by creation time (newest first)
- The latest deployment's Reasoning Engine ID
- Instructions to update your `.env` file

### Finding the ID in Console

The Reasoning Engine ID is the last part of the Resource name:
```
projects/123456789/locations/us-central1/reasoningEngines/6686143402645389312
                                                          ^^^^^^^^^^^^^^^^^^^^
                                                          This is the ID
```

## Updating Your Configuration

After identifying the latest deployment:

1. **Update `.env` file**:
   ```bash
   # In bq_agent_mick/.env
   REASONING_ENGINE_ID=6686143402645389312
   ```

2. **Update query scripts**:
   ```python
   # In bq_agent_mick/query_agent.py or test_agent.py
   REASONING_ENGINE_ID = "6686143402645389312"
   ```

## Cleaning Up Old Deployments

### Manual Cleanup (Console)

1. Go to [Vertex AI Agent Engine Console](https://console.cloud.google.com/vertex-ai/agents/agent-engines)
2. Select old deployments (checkboxes)
3. Click "Delete"
4. Confirm deletion

### Automated Cleanup (Script)

Keep only the latest deployment:

```bash
# Dry run (see what would be deleted)
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1 DRY_RUN=1

# Actually delete (keeps only 1 latest)
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1

# Keep the 2 latest deployments
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=2
```

Or use the script directly:

```bash
# Dry run
python scripts/cleanup_old_deployments.py \
    --agent-name bq_agent_mick \
    --keep 1 \
    --dry-run

# Actually delete
python scripts/cleanup_old_deployments.py \
    --agent-name bq_agent_mick \
    --keep 1
```

### Force Delete Deployments with Active Sessions

Sometimes deployments can't be deleted because they have active sessions (even if there "shouldn't be anything" holding them). You can force delete these deployments:

```bash
# Force delete (removes child resources/sessions)
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1 FORCE=1

# Or with dry-run first to preview
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1 FORCE=1 DRY_RUN=1

# Using the script directly
python scripts/cleanup_old_deployments.py \
    --agent-name bq_agent_mick \
    --keep 1 \
    --force
```

**When to use `--force`:**
- You see "Has active sessions" errors when trying to delete
- You know there are no real active sessions (stuck/stale sessions)
- You want to immediately clean up old deployments without waiting for sessions to expire

**Note:** Force deletion will delete child resources (sessions) along with the deployment. This is safe if you're cleaning up old deployments.

### Inspecting Deployments

To see what might be holding onto a deployment:

```bash
# Inspect a specific deployment
python scripts/inspect_deployment.py --engine-id <REASONING_ENGINE_ID>

# Example
python scripts/inspect_deployment.py --engine-id 6686143402645389312
```

This will show:
- Deployment details (name, created time, age)
- Active operations (if any)
- Detailed error messages if deletion fails
- Recommendations for troubleshooting

**Use this when:**
- A deployment can't be deleted and you want to understand why
- You want to see deployment metadata (age, creation time, etc.)
- You're troubleshooting deployment issues

### Cleanup Best Practices

1. **During Development**: Keep 2-3 latest deployments (in case latest has issues)
2. **After Stabilizing**: Keep only 1 (the production deployment)
3. **Before Major Changes**: Keep 1 old deployment as backup

## Deployment Workflow Recommendations

### Development Phase

```bash
# 1. Deploy
make deploy-bq-agent-mick

# 2. Check latest deployment
make list-deployments AGENT_NAME=bq_agent_mick

# 3. Update REASONING_ENGINE_ID in .env
# (Edit bq_agent_mick/.env with the latest ID)

# 4. Test
python -m bq_agent_mick.query_agent "Your question"
```

### Production Deployment

```bash
# 1. Clean up old dev deployments (keep 1)
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1

# 2. Deploy production version
make deploy-bq-agent-mick

# 3. Verify and update configuration
make list-deployments AGENT_NAME=bq_agent_mick
# Update REASONING_ENGINE_ID
```

## Cost Considerations

Each Reasoning Engine instance:
- **Costs money** while active (even if not used)
- Takes up **quota** in your project
- Should be **cleaned up** when no longer needed

Old deployments that aren't being used should be deleted to:
- Reduce costs
- Free up quota
- Keep the console clean

## Troubleshooting

### "Which deployment should I use?"

Use the **newest** one (highest in the list when sorted by "Created").

### "Can I update an existing deployment?"

No. Each deployment is immutable. You must create a new one and delete the old one.

### "Do old deployments still work?"

Yes, old deployments remain functional. They just won't have your latest code changes.

### "How do I know which deployment is active?"

Check your `.env` file or query scripts for the `REASONING_ENGINE_ID`. That's the one that's being used.

### "Why can't I delete a deployment? It says 'Has active sessions'"

Deployments can have active sessions that prevent deletion. This can happen even if you think there are no active sessions (stuck/stale sessions).

**Options:**
1. **Force delete** (recommended for old deployments):
   ```bash
   make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1 FORCE=1
   ```

2. **Wait for sessions to expire** (typically 30-60 minutes of inactivity)

3. **Delete via Console** (may have force-delete option)

4. **Inspect the deployment** to understand what's holding it:
   ```bash
   python scripts/inspect_deployment.py --engine-id <ID>
   ```

### "What holds onto deployments?"

Deployments can be held by:
- **Active sessions** - Client connections that haven't expired yet
- **Stuck/stale sessions** - Sessions that didn't properly close (can happen during development)
- **Ongoing operations** - Long-running operations associated with the deployment

Most commonly, it's sessions (active or stale). Use `--force` to delete deployments with sessions.

## Quick Reference

```bash
# List all deployments
make list-deployments

# List specific agent
make list-deployments AGENT_NAME=bq_agent_mick

# Clean up (keep 1 latest)
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1

# Clean up (dry run)
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1 DRY_RUN=1

# Force delete (removes deployments with active sessions)
make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1 FORCE=1

# Inspect a deployment
python scripts/inspect_deployment.py --engine-id <ID>
```

## Related Documentation

- [bq_agent_mick Deployment Guide](./bq_agent_mick_deployment.md)
- [bq_agent_mick Usage Guide](./bq_agent_mick_usage.md)
