import asyncio
import bq_agent.agent as agent
import constants
from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
import google.cloud.bigquery
from google.genai import types
import json

load_dotenv()

APP_NAME = "agents"
USER_ID = "gap-billing-agent@qwiklabs-asl-04-8e9f23e85ced.iam.gserviceaccount.com"
SESSION_ID = "session_001"

def get_data_from_bq(query):
    data = []
    client = google.cloud.bigquery.Client(project=constants.PROJECT_ID)
    try:
        query_response = client.query(query)
        while query_response.state != 'DONE':
            query_response.result()
        
        for table_row in list(query_response.result()):
            row = {}
            table_fields = table_row.keys()
            for field in table_fields:
                row[field] = table_row[field]
            data.append(row)
    except Exception as e:
        print(f"Error: {e}")
    return data

async def load_agent():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(
        agent=agent.root_agent,  # The agent we want to run
        app_name=APP_NAME,  # Associates runs with our app
        session_service=session_service,  # Uses our session manager
    )
    return {"runner": runner, "session": session}

async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query: {query}")
    content = types.Content(role="user", parts=[types.Part(text=query)])
    final_response_text = "Agent did not produce a final response."  # Default
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        # You can uncomment the line below to see *all* events during execution
        # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif (
                event.actions and event.actions.escalate
            ):  # Handle potential errors/escalations
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            # Add more checks here if needed (e.g., specific error codes)
            break  # Stop processing events once the final response is found

    print(f"<<< Agent Response: {final_response_text}")

if __name__ == "__main__":
    agent_metadata = asyncio.run(load_agent())
    print(agent_metadata)
    runner = agent_metadata["runner"]
    session = agent_metadata["session"]
    # query = "Could you give me the top 10 services by highest cost spendings? Please output the results in tabular format"
    query = "Could you give me the projects with highest month to month cost spendings for the months of september to october of 2025? Please output the results in tabular format"
    asyncio.run(call_agent_async(query, runner, USER_ID, SESSION_ID))
    TABLE_ID = '.'.join([constants.PROJECT_ID, constants.DATASET_NAME, constants.TABLE_NAME])
    print(TABLE_ID)
    # test_query = f"SELECT tla, SUM(cost) as total_cost FROM `{TABLE_ID}` WHERE invoice_month = '202510' GROUP BY ALL ORDER BY SUM(cost) DESC LIMIT 3"
    test_query = f"""
        SELECT 
            a.project_id, b.total_cost, a.total_cost, a.total_cost-b.total_cost as metric
        FROM 
            (SELECT project_id, SUM(cost) as total_cost FROM`{TABLE_ID}` WHERE invoice_month = '202510' GROUP BY 1) a,
            (SELECT project_id, SUM(COST) as total_cost FROM`{TABLE_ID}` WHERE invoice_month = '202509' GROUP BY 1) b
        WHERE a.project_id = b.project_id
        ORDER BY metric DESC
        LIMIT 10
    """
    result = get_data_from_bq(test_query)
    print("Result from human query:")
    for row in result:
        print(json.dumps(row))