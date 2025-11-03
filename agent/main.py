import agent
import importlib

importlib.reload(agent)  # Force reload

# Example tool usage (optional test)
print(agent.test_agent(2))
print(agent.test_agent("Paris"))