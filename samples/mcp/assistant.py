import asyncio

from genpilot.agent import Agent
from genpilot.chat import TerminalChat

from dotenv import load_dotenv

load_dotenv()

import logging

logging.basicConfig(level=logging.WARNING)

# Set logging level to WARNING or higher to suppress INFO level logs
import logging
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
        tools=[final_answer],
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
