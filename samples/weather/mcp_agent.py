import asyncio

from genpilot.mcp.agent import Agent
from genpilot.mcp.chat import TerminalChat

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
    terminal = TerminalChat(model_options={"temperature": 0.2, "stream": False})

    agent = Agent(
        name="Weather Observer",
        model="groq/llama-3.3-70b-versatile",
        chat=terminal,
        system="You are an AI assistant",
    )
    logging.basicConfig(level=logging.WARNING)
    try:
        await agent.connect_to_server(sys.argv[1])
        await agent.chatbot()
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
