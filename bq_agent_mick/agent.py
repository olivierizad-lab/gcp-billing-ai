import os
import google.auth
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig

PROJECT_ID = os.environ.get("BQ_PROJECT", "qwiklabs-asl-04-8e9f23e85ced")
DATASET    = os.environ.get("BQ_DATASET", "qwiklabs-asl-04-8e9f23e85ced.gcp_billing_data")
LOCATION   = os.environ.get("BQ_LOCATION", "US")

credentials, _ = google.auth.default()

bq_tools = BigQueryToolset(
    credentials_config=BigQueryCredentialsConfig(credentials=credentials)
)

async def _build_root_agent():
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

# --- same sync wrapper from earlier (works under ADK CLI and python -m) ---
def _build_root_agent_sync():
    import asyncio
    try:
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_build_root_agent())
    except RuntimeError:
        return asyncio.run(_build_root_agent())

root_agent = _build_root_agent_sync()
