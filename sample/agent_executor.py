import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import GroqClient, BedRockClient
from tool import execute_code, Permission
from agent import Agent
from client.aws_bedrock import BedRockClient

a = Agent(
    BedRockClient(),
    "Assistant AI",
    "You are an assistant to solve tasks. You can use the code executor write python code to do that",
    tools=[execute_code],
    debug=True,
    permission=Permission.AUTO,
)

a(
    "Plot a chart of NVDA and TESLA stock prices YTD in the latest 1 year, with step 1 month"
)
