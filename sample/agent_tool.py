import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import BedRockClient, GroqClient
from tool import wikipedia, Permission
from agent import Agent


def llama32_90b_client():
    return BedRockClient(
        "us.meta.llama3-2-90b-instruct-v1:0",
        {"maxTokens": 2000, "temperature": 0.2},
        0.002,  # $0.002 per 1000 input tokens
        0.002,  # $0.002 per 1000 output tokens
    )


a = Agent(
    GroqClient(),
    "Assistant AI",
    "You are an assistant to solve tasks, Before give a tool or function action, please give a assistant response to show your thought about it",
    tools=[wikipedia],
    permission=Permission.ALWAYS,
    structured_output=False,  # no structured output isn't supported by BedRockClient,
)

prompt = sys.argv[1]
a.run(prompt)
