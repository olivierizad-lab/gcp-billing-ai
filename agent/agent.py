from google.adk.agents import Agent

MODEL = "gemini-2.0-flash"

from .tools import test_agent

root_agent = Agent(
    name="test_agent_v1",
    model=MODEL, # Can be a string for Gemini or a LiteLlm object
    description="Testing the agent.",
    instruction="You are a helpful arithmetic agent. " \
                "When the user calls the test_agent function, use the function to find the information. " \
                "If the tool returns an error, inform the use politely. " \
                "If the tool is successful, present the result clearly",
    tools=[test_agent], # Pass the function directly
)

