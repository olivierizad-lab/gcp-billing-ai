from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
from google.genai import types

# Define constants for this example agent
AGENT_NAME = "bigquery_agent"
APP_NAME = "bigquery_app"
USER_ID = "gap-billing-agent@qwiklabs-asl-04-8e9f23e85ced.iam.gserviceaccount.com"
SESSION_ID = "session_001"
GEMINI_MODEL = "gemini-2.0-flash"

# Define a tool configuration to block any write operations
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

# Uses externally-managed Application Default Credentials (ADC) by default.
# This decouples authentication from the agent / tool lifecycle.
# https://cloud.google.com/docs/authentication/provide-credentials-adc
# credentials_config = BigQueryCredentialsConfig()

# Instantiate a BigQuery toolset
bigquery_toolset = BigQueryToolset(
    # credentials_config=credentials_config, 
    bigquery_tool_config=tool_config
)

# Agent Definition
root_agent = Agent(
    model=GEMINI_MODEL,
    name=AGENT_NAME,
    description=(
        "Agent to answer questions about BigQuery data and models and execute"
        " SQL queries."
    ),
    instruction="""\
        You are a data science agent with access to several BigQuery tools.
        Be an assistant that will automatically map the questions to a query.
        Make use of those tools to answer the user's questions.
        All data is in this table: qwiklabs-asl-04-8e9f23e85ced.billing_dataset.fake_billing_data
        You should always call get_table_info to retrieve the schema from this table.
    """,
    tools=[bigquery_toolset],
)

