import os
import google.auth
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig

PROJECT_ID = os.environ.get("BQ_PROJECT", "qwiklabs-asl-04-8e9f23e85ced")
DATASET    = os.environ.get("BQ_DATASET", "qwiklabs-asl-04-8e9f23e85ced.gcp_billing_data")
LOCATION   = os.environ.get("BQ_LOCATION", "US")

# Initialize credentials - handle errors gracefully for Agent Engine
# For Agent Engine, credentials are managed by the platform, so we'll rely on ADC
try:
    credentials, _ = google.auth.default()
    # Use explicit credentials if available (for local dev)
    bq_tools = BigQueryToolset(
        credentials_config=BigQueryCredentialsConfig(credentials=credentials)
    )
except Exception as cred_error:
    # In Agent Engine, credentials are handled automatically via ADC
    # Fall back to default toolset (uses implicit ADC)
    bq_tools = BigQueryToolset()

async def _build_root_agent():
    """Build the agent asynchronously (for async contexts)."""
    tools = await bq_tools.get_tools()        # returns a list of tools
    # (defensive) keep only BigQuery tools in case any extra packages remain
    tools = [t for t in tools if "bigquery" in getattr(t, "name", "").lower()]
    return Agent(
        name="bq_agent_mick",
        model="gemini-2.5-flash",
        description="Answers questions by inspecting BigQuery metadata and running SQL.",
        instruction=(f"Project: {PROJECT_ID} (location {LOCATION}). Prefer dataset {DATASET}."),
        tools=tools,
    )

def _build_root_agent_sync():
    """Build the agent synchronously (for sync contexts and Agent Engine)."""
    import asyncio
    try:
        # Try with nest_asyncio first (for environments with existing event loops)
        import nest_asyncio
        nest_asyncio.apply()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to use nest_asyncio
                return loop.run_until_complete(_build_root_agent())
            else:
                return asyncio.run(_build_root_agent())
        except RuntimeError:
            return asyncio.run(_build_root_agent())
    except ImportError:
        # nest_asyncio not available, use asyncio.run
        return asyncio.run(_build_root_agent())
    except Exception as e:
        # If all else fails, try direct creation without async tools
        # This is a fallback for Agent Engine compatibility
        print(f"Warning: Async agent build failed ({e}), trying direct toolset creation...")
        try:
            # Fallback: create agent directly with toolset (no async tool retrieval)
            return Agent(
                name="bq_agent_mick",
                model="gemini-2.5-flash",
                description="Answers questions by inspecting BigQuery metadata and running SQL.",
                instruction=(f"Project: {PROJECT_ID} (location {LOCATION}). Prefer dataset {DATASET}."),
                tools=[bq_tools],  # Use toolset directly instead of individual tools
            )
        except Exception as fallback_error:
            raise RuntimeError(f"Failed to build agent: {e}. Fallback also failed: {fallback_error}")

# Create the root agent - Agent Engine expects this to be available
# Use sync wrapper to ensure it works in all contexts
# Wrap in try-except to provide better error messages
try:
    root_agent = _build_root_agent_sync()
except Exception as e:
    print(f"Error creating root_agent: {e}")
    import traceback
    traceback.print_exc()
    raise
