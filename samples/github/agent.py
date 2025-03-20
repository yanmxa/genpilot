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
        result = await Runner.run(
            agent,
            "list all the opening pr in this repos: https://github.com/stolostron/multicluster-global-hub",
        )
        print(result.final_output)
        # print(mcp_server_tools)


if __name__ == "__main__":
    asyncio.run(main())

"""
$ python samples/github/agent.py ./samples/github/mcp-server-config.json

"""
