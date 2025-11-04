import asyncio
import bq_agent.agent as agent
import constants
from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
import google.cloud.bigquery
from google.genai import types
import json
import re

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
    return final_response_text

def load_data(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def parse_agent_response2(agent_response_text):
    lines = agent_response_text.split("\n")
    data = []
    first_line_found = False
    second_line_found = False
    for line in lines:
        if re.match("^\+\-+\+.*", line) and not first_line_found:
            first_line_found = True
            continue
        if re.match("^\+\-+\+.*", line) and not second_line_found:
            second_line_found = True
            continue
        if re.match("^```", line) and second_line_found:
            break
        if second_line_found:
            data.append(re.split(" +\| +", re.sub(" +\|$", "", re.sub("^\| +", "", line))))
    return data

def parse_agent_response(agent_response_text):
    if re.match(".*\n\+\-+\+.*", agent_response_text):
        return parse_agent_response2(agent_response_text)
    lines = agent_response_text.split("\n")
    data = []
    first_line_found = False
    for line in lines:
        if re.match("^\|\-|\+.*", line) and not first_line_found:
            first_line_found = True
            continue
        if re.match("^```", line) and first_line_found:
            break
        if first_line_found:
            content = re.split(" +\| +", re.sub(" +\|$", "", re.sub("^\| +", "", line)))
            if len(content) > 0 and len(content[0]) > 0:
                data.append(content)
    return data

if __name__ == "__main__":
    prompts_and_queries = load_data("candidate_questions.json")
    agent_metadata = asyncio.run(load_agent())
    print(agent_metadata)
    runner = agent_metadata["runner"]
    session = agent_metadata["session"]
    for line in prompts_and_queries:
        prompt = line["prompt"]
        query = line["query"]

        # Result from Agent
        print("Result from agent:")
        agent_response_text = asyncio.run(call_agent_async(prompt, runner, USER_ID, SESSION_ID))
        agent_data = parse_agent_response(agent_response_text)
        # Result from BigQuery
        result = get_data_from_bq(query)
        print("Result from human query:")
        print(query)
        keys = list(result[0].keys())
        agent_validation = True
        for i in range(len(result)):
            row = result[i]
            validation = row[keys[0]] == agent_data[i][0] and round(row[keys[1]],2) == round(float(agent_data[i][1]),2)
            agent_validation = agent_validation and validation
            print(f"{row[keys[0]]}\t{row[keys[1]]}\tvalidation={validation}")

        print(f"\nWas the Agent correct? {agent_validation}")
        print("-"*28 + "\n")
