import os
import google.auth
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode

PROJECT_ID = os.environ.get("BQ_PROJECT", "qwiklabs-asl-04-8e9f23e85ced")
DATASET    = os.environ.get("BQ_DATASET", "qwiklabs-asl-04-8e9f23e85ced.gcp_billing_data")
TABLE_NAME = os.environ.get("BQ_TABLE", "billing_data_ndjson")
FULL_TABLE_PATH = f"{PROJECT_ID}.gcp_billing_data.{TABLE_NAME}"
LOCATION   = os.environ.get("BQ_LOCATION", "US")

# Initialize credentials - handle errors gracefully for Agent Engine
# For Agent Engine, credentials are managed by the platform, so we'll rely on ADC
# Configure BigQuery toolset with write blocking for security
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

try:
    credentials, _ = google.auth.default()
    # Use explicit credentials if available (for local dev)
    bq_tools = BigQueryToolset(
        credentials_config=BigQueryCredentialsConfig(credentials=credentials),
        bigquery_tool_config=tool_config
    )
except Exception as cred_error:
    # In Agent Engine, credentials are handled automatically via ADC
    # Fall back to default toolset (uses implicit ADC) but still block writes
    bq_tools = BigQueryToolset(bigquery_tool_config=tool_config)

async def _build_root_agent():
    """Build the agent asynchronously (for async contexts)."""
    tools = await bq_tools.get_tools()        # returns a list of tools
    # (defensive) keep only BigQuery tools in case any extra packages remain
    tools = [t for t in tools if "bigquery" in getattr(t, "name", "").lower()]
    return Agent(
        name="bq_agent_mick",
        model="gemini-2.5-flash",
        description="Answers questions by inspecting BigQuery metadata and running SQL.",
        instruction=f"""You are a data science agent with access to BigQuery tools.

Project: {PROJECT_ID} (location {LOCATION})
Dataset: {DATASET}
Main table: {FULL_TABLE_PATH}

IMPORTANT: All billing data is in the table {FULL_TABLE_PATH}. This is the primary table you should query.

Your workflow should be:
1. Always call get_table_info first to retrieve the schema from {FULL_TABLE_PATH}
2. Use the schema to understand the table structure
3. Show the SQL query you plan to execute BEFORE running it (e.g., "I'll run this query: SELECT ...")
4. IMMEDIATELY execute the SQL query using execute_query tool - do NOT stop after showing the SQL
5. Present results in a clear, readable format (preferably tabular)

CRITICAL RULES:
- ALWAYS display the SQL query you're about to run before executing it
- ALWAYS execute the query using execute_query tool after showing it - never skip execution
- You must complete both showing the query AND executing it - showing alone is not sufficient
- Always query the table directly - do not cache data from previous questions
- Use efficient SQL queries with appropriate filters and aggregations
- The table contains GCP billing data with fields like cost, service, project, invoice_month, etc.
- When asked about costs, services, projects, or billing patterns, query {FULL_TABLE_PATH}
- Explain your approach when helpful, especially for complex queries
- Format SQL queries in a readable way (with line breaks for complex queries)

BigQuery Formatting for Currency:
- For US currency with 2 decimal places: CONCAT('$', FORMAT('%.2f', value))
- For currency with thousands separators: CONCAT('$', FORMAT('%,.2f', value))
- BigQuery FORMAT uses printf-style strings: '%.2f' = 2 decimals, '%,.2f' = commas + 2 decimals
- If FORMAT fails, use: CONCAT('$', CAST(ROUND(value, 2) AS STRING))
- IMPORTANT: Test ONE query with correct formatting - do not iterate through multiple format attempts
- The correct format is usually: CONCAT('$', FORMAT('%.2f', SUM(cost))) for basic currency""",
        tools=tools,
    )

def _build_root_agent_direct():
    """Build agent directly with toolset (no async operations - Agent Engine compatible)."""
    # Create agent directly with toolset - this works in all contexts
    # The toolset will be converted to tools when the agent runs
    return Agent(
        name="bq_agent_mick",
        model="gemini-2.5-flash",
        description="Answers questions by inspecting BigQuery metadata and running SQL.",
        instruction=f"""You are a data science agent with access to BigQuery tools.

Project: {PROJECT_ID} (location {LOCATION})
Dataset: {DATASET}
Main table: {FULL_TABLE_PATH}

IMPORTANT: All billing data is in the table {FULL_TABLE_PATH}. This is the primary table you should query.

Your workflow should be:
1. Always call get_table_info first to retrieve the schema from {FULL_TABLE_PATH}
2. Use the schema to understand the table structure
3. Show the SQL query you plan to execute BEFORE running it (e.g., "I'll run this query: SELECT ...")
4. IMMEDIATELY execute the SQL query using execute_query tool - do NOT stop after showing the SQL
5. Present results in a clear, readable format (preferably tabular)

CRITICAL RULES:
- ALWAYS display the SQL query you're about to run before executing it
- ALWAYS execute the query using execute_query tool after showing it - never skip execution
- You must complete both showing the query AND executing it - showing alone is not sufficient
- Always query the table directly - do not cache data from previous questions
- Use efficient SQL queries with appropriate filters and aggregations
- The table contains GCP billing data with fields like cost, service, project, invoice_month, etc.
- When asked about costs, services, projects, or billing patterns, query {FULL_TABLE_PATH}
- Explain your approach when helpful, especially for complex queries
- Format SQL queries in a readable way (with line breaks for complex queries)

BigQuery Formatting for Currency:
- For US currency with 2 decimal places: CONCAT('$', FORMAT('%.2f', value))
- For currency with thousands separators: CONCAT('$', FORMAT('%,.2f', value))
- BigQuery FORMAT uses printf-style strings: '%.2f' = 2 decimals, '%,.2f' = commas + 2 decimals
- If FORMAT fails, use: CONCAT('$', CAST(ROUND(value, 2) AS STRING))
- IMPORTANT: Test ONE query with correct formatting - do not iterate through multiple format attempts
- The correct format is usually: CONCAT('$', FORMAT('%.2f', SUM(cost))) for basic currency""",
        tools=[bq_tools],  # Use toolset directly - ADK will handle tool extraction
    )

def _build_root_agent_sync():
    """Build the agent synchronously (for sync contexts and Agent Engine)."""
    import asyncio
    
    # Check if there's already a running event loop (Agent Engine has one)
    has_running_loop = False
    try:
        loop = asyncio.get_running_loop()
        has_running_loop = True
    except RuntimeError:
        # No running loop - safe to use asyncio.run
        has_running_loop = False
    
    if has_running_loop:
        # There's a running loop (Agent Engine context) - fall back to direct creation
        # Don't use nest_asyncio in Agent Engine - it's not reliably available
        # Direct creation works better in this context
        return _build_root_agent_direct()
    else:
        # No running loop - try asyncio.run, fall back to direct if needed
        try:
            return asyncio.run(_build_root_agent())
        except Exception:
            # If asyncio.run fails, use direct creation
            return _build_root_agent_direct()

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


# Note: When using 'adk deploy agent_engine', the deployment process wraps
# root_agent in an AdkApp instance which automatically provides 'query' and
# 'stream_query' methods. We don't need to define them manually.
# 
# The AdkApp wrapper handles:
# - Converting REST API requests to agent queries
# - Session management
# - Streaming responses
# - Error handling
#
# Just ensure root_agent is properly defined and exported.
