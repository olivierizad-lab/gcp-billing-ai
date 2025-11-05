# Deployment Automation - Cloud Run-like Behavior

## Overview

The deployment process now automatically manages old deployments, similar to how Cloud Run handles revisions. By default, when you deploy an agent, it will:

1. **Deploy** the new version
2. **Clean up** old deployments, keeping only the latest (default: 1)

This ensures you don't accumulate many old deployments and keeps your environment clean.

## Default Behavior (Cloud Run-like)

When you deploy, old deployments are automatically cleaned up **after** successful deployment:

```bash
# Deploy and automatically clean up old deployments (keeps latest 1)
make deploy-bq-agent-mick

# Or using the script directly
python scripts/deploy_agent_engine.py --agent-dir bq_agent_mick
```

**What happens:**
1. ✅ Deploys new version
2. ✅ After success, deletes old deployments (keeps latest 1)
3. ✅ You're left with just the new deployment

## Customization Options

### Keep More Deployments

To keep multiple deployments (like keeping last 3 revisions):

```bash
# Keep latest 3 deployments
make deploy-bq-agent-mick KEEP=3

# Or using script
python scripts/deploy_agent_engine.py --agent-dir bq_agent_mick --keep 3
```

### Cleanup Before Deploying

Clean up old deployments **before** deploying (useful if you want to free up quota first):

```bash
# Cleanup first, then deploy
make deploy-bq-agent-mick CLEANUP_BEFORE=1

# Or using script
python scripts/deploy_agent_engine.py --agent-dir bq_agent_mick --cleanup-before
```

### Skip Cleanup

If you want to keep all deployments (for testing/comparison):

```bash
# Deploy without cleanup
make deploy-bq-agent-mick NO_CLEANUP=1

# Or using script
python scripts/deploy_agent_engine.py --agent-dir bq_agent_mick --no-cleanup
```

## Complete Options Reference

### Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KEEP` | `1` | Number of latest deployments to keep |
| `CLEANUP_BEFORE` | (unset) | Set to `1` to cleanup before deploying |
| `NO_CLEANUP` | (unset) | Set to `1` to skip cleanup entirely |

### Script Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--keep N` | `1` | Keep N latest deployments when cleaning |
| `--cleanup-before` | `False` | Clean up old deployments before deploying |
| `--no-cleanup` | `False` | Skip cleanup after deployment |

## Examples

### Standard Deployment (Recommended)
```bash
# Deploy and cleanup automatically (keeps latest 1)
make deploy-bq-agent-mick
```

### Keep Multiple Versions
```bash
# Keep last 3 deployments for rollback capability
make deploy-bq-agent-mick KEEP=3
```

### Cleanup First
```bash
# Clean up old deployments first, then deploy
make deploy-bq-agent-mick CLEANUP_BEFORE=1
```

### Development Mode (No Cleanup)
```bash
# Deploy without cleanup (keep all versions for testing)
make deploy-bq-agent-mick NO_CLEANUP=1
```

### Combined Options
```bash
# Cleanup before, keep 2 latest, deploy
make deploy-bq-agent-mick CLEANUP_BEFORE=1 KEEP=2
```

## What Happens with Active Sessions?

If a deployment has active sessions, it cannot be deleted immediately. The cleanup process will:

- ✅ Skip deployments with active sessions
- ⚠️ Show a warning message
- ℹ️ Provide guidance to wait and retry later

Sessions typically expire after 30-60 minutes of inactivity. See [Session Management](./session_management.md) for details.

## Comparison with Cloud Run

| Feature | Cloud Run | Agent Engine (with cleanup) |
|---------|-----------|----------------------------|
| Auto-cleanup | ✅ Yes | ✅ Yes (after deployment) |
| Keep N revisions | ✅ Yes | ✅ Yes (via `--keep N`) |
| Update in place | ✅ Yes | ⚠️ Creates new, deletes old |
| Rollback | ✅ Easy | ✅ Keep multiple versions |

## Best Practices

1. **Use default behavior** for production: `make deploy-bq-agent-mick` (keeps latest 1)

2. **Keep 2-3 versions** during development for easy rollback:
   ```bash
   make deploy-bq-agent-mick KEEP=3
   ```

3. **Cleanup before deploying** if you're hitting quota limits:
   ```bash
   make deploy-bq-agent-mick CLEANUP_BEFORE=1
   ```

4. **Skip cleanup** during active testing/comparison:
   ```bash
   make deploy-bq-agent-mick NO_CLEANUP=1
   ```

5. **Manual cleanup** if needed:
   ```bash
   make cleanup-deployments AGENT_NAME=bq_agent_mick KEEP=1
   ```

## Related Documentation

- [Session Management](./session_management.md) - Understanding active sessions
- [Deployment Management](./deployment_management.md) - Manual deployment management
