import asyncio

from genpilot.agent import Agent
from genpilot.chat import TerminalChat

from dotenv import load_dotenv

load_dotenv()

import logging

logging.basicConfig(level=logging.WARNING)

# Set logging level to WARNING or higher to suppress INFO level logs
import logging


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    terminal = TerminalChat()

    agent = Agent(
        name="Assistant",
        chat=terminal,
        model_config={
            "name": "groq/llama-3.3-70b-versatile",
            "config": {"temperature": 0.2, "stream": False},
        },
        system="You are an AI assistant, If you finished the task, just return the answer in the content",
    )
    try:
        await agent.register_server_tools(sys.argv[1])
        await agent()
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
