import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import Client
from tool import wikipedia, Permission
from agent import Agent

a = Agent(
    Client(),
    "Assistant AI",
    "You are an assistant to solve tasks",
    tools=[wikipedia],
    debug=True,
    permission=Permission.ALWAYS,
)

a("When was Red Hat founded?")
