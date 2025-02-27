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

    # model_options: https://platform.openai.com/docs/api-reference/chat/create
    terminal = TerminalChat()

    agent = Agent(
        name="Weather Observer",
        model_name="groq/llama-3.3-70b-versatile",
        chat=terminal,
        model_config={"temperature": 0.2, "stream": False},
        system="You are an AI assistant",
    )
    try:
        await agent.register_server_tools(sys.argv[1])
        result = await agent()
        # print(f"the result {result}")
        await asyncio.sleep(1)
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
