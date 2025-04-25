#!/usr/bin/env python3

import asyncio
import sys
from agents import Agent, Runner

from genpilot.mcp.manager import MCPServerManager

from dotenv import load_dotenv

load_dotenv()


async def main():
    async with MCPServerManager(sys.argv[1]) as server_manager:
        mcp_server_tools = await server_manager.function_tools()
        agent = Agent(
            name="assistant",
            instructions="You are an AI assistant.",
            tools=mcp_server_tools,
        )
        result = await Runner.run(agent, "List all the kubernetes clusters")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())

"""
$ python samples/mcp/agent.py ./samples/mcp/assistant-server-config.json

Here are the Kubernetes clusters available:

1. **cluster1**
   - Hub Accepted: True
   - Managed Cluster URL: https://api.....com:6443
   - Joined: True
   - Available: True
   - Age: 30 days

2. **cluster2**
   - Hub Accepted: True
   - Managed Cluster URL: https://api.....com:6443
   - Joined: True
   - Available: True
   - Age: 30 days
"""
