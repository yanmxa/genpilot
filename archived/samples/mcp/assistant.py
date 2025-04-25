#!/usr/bin/env python3
"""
Usage:
    python samples/mcp/assistant.py ./samples/mcp/assistant-server-config.json

Description:
    This script starts the assistant using the MCP server with the provided configuration file.
"""

import asyncio

from genpilot.agent import Agent
from genpilot.chat import TerminalChat

from dotenv import load_dotenv

load_dotenv()

import logging

logging.basicConfig(level=logging.WARNING)

from genpilot.abc.agent import ActionPermission, final_answer


def terminal_list_cluster_printer(agent, func_name, func_args):
    import rich

    console = rich.get_console()
    console.print(f"   🛠  [yellow]Managed Clusters[/yellow] ⎈ ")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    terminal = TerminalChat()
    # beautiful printing
    terminal.register_tool_printer(
        func_name="clusters", printer=terminal_list_cluster_printer
    )

    agent = Agent(
        name="Assistant",
        chat=terminal,
        model_config={
            "name": "groq/llama-3.3-70b-specdec",
            "config": {"temperature": 0.2, "stream": False},
        },
        system="You are an AI assistant.",
        mcp_server_config=sys.argv[1],
        tools=[],
        action_permission=ActionPermission.NONE,
        human_on_loop=False,
    )

    try:
        await agent.connect_to_mcp_server()
        await agent.chatbot()
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
