import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import BedRockClient, GroqClient
from tool import wikipedia, execute_code
from agent import DefaultAgent


def llama32_90b_client():
    return BedRockClient(
        "us.meta.llama3-2-90b-instruct-v1:0",
        {"maxTokens": 2000, "temperature": 0.2},
        0.002,  # $0.002 per 1000 input tokens
        0.002,  # $0.002 per 1000 output tokens
    )


async def main():
    prompt = sys.argv[1]
    a = DefaultAgent(
        GroqClient(),
        "Assistant AI",
        "You are an assistant to solve tasks, Before give a tool or function action, please give a assistant response to show your thought about it",
        tools=[wikipedia, execute_code],
    )
    response = await a.run(prompt)


if __name__ == "__main__":
    asyncio.run(main())
