import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import BedRockClient
from tool import execute_code, Permission
from agent import Agent
from client.aws_bedrock import BedRockClient


def claude35_sonnet_client():
    return BedRockClient(
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        {"maxTokens": 1000, "temperature": 0.2},
        0.003,  # $0.003 per 1000 input tokens
        0.015,  # $0.015 per 1000 output tokens
    )


def llama32_90b_client():
    return BedRockClient(
        "us.meta.llama3-2-90b-instruct-v1:0",
        {"maxTokens": 2000, "temperature": 0.2},
        0.002,  # $0.002 per 1000 input tokens
        0.002,  # $0.002 per 1000 output tokens
    )


a = Agent(
    llama32_90b_client(),
    "Assistant AI",
    "You are an assistant to solve tasks. You can use the code executor write python code to do that",
    tools=[execute_code],
    debug=True,
    permission=Permission.AUTO,
)

prompt = sys.argv[1]
a(prompt)
