import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tool import execute_code, Permission
from agent import PromptAgent
from client import BedRockClient, GroqClient


def llama32_90b_client():
    return BedRockClient(
        "us.meta.llama3-2-90b-instruct-v1:0",
        {"maxTokens": 2000, "temperature": 0.2},
        0.002,  # $0.002 per 1000 input tokens
        0.002,  # $0.002 per 1000 output tokens
    )


a = PromptAgent(
    llama32_90b_client(),
    "Assistant AI",
    "You are an assistant to solve tasks. You can use the code executor write python code to do that",
    tools=[execute_code],
    permission=Permission.ALWAYS,
)

prompt = sys.argv[1]
a.run(prompt)
