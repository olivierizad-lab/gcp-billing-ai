"""
Agent Engine application wrapper for bq_agent_mick.

This file is used by 'adk deploy agent_engine' to properly wrap the agent
in an AdkApp instance for Agent Engine deployment.
"""

from vertexai.preview.reasoning_engines import AdkApp
from bq_agent_mick.agent import root_agent

# Wrap the agent in AdkApp for Agent Engine deployment
# AdkApp automatically provides query() and stream_query() methods
# Set explicit app_name to avoid "App name mismatch" warnings
adk_app = AdkApp(
    agent=root_agent,
    app_name="bq_agent_mick_app",  # Explicit app name to avoid conflicts
    enable_tracing=False,
)
