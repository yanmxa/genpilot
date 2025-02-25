import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import BedRockClient, GroqClient
from tools import wikipedia, code_executor
from client.config import ClientConfig
import instructor
from type import ChatMessage

from dotenv import load_dotenv

load_dotenv()


groq_client = GroqClient(
    ClientConfig(
        model="llama3-70b-8192",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY"),
        mode=instructor.Mode.JSON,
    )
)

messages = [
    {
        "role": "system",
        "content": "Your are an ai assistant help the resolve the task. No tools are available. ",
    },
    {"role": "user", "content": "when the redhat is founded?"},
]
messages = [
    {
        "role": "system",
        "content": "Your are an ai assistant help the resolve the task. Available tools: Wikipedia tool, evenry time you receive a task, when you don't known the something, try to use the tool before give the answer",
    },
    {"role": "user", "content": "when the tttt is founded?"},
]
response, _ = groq_client(
    messages,
    tools=None,
    response_model=ChatMessage,
)

import rich

rich.print(response)
