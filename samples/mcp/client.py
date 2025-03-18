import asyncio
import sys

# import logging

from genpilot.mcp.manager import MCPServerManager


# logging.basicConfig(level=logging.DEBUG)


# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[
#         logging.FileHandler("app.log"),  # Save to file
#         logging.StreamHandler(),  # Print to console
#     ],
# )


# simplicity
async def with_async_context():
    async with MCPServerManager(sys.argv[1]) as sessionManager:
        schemas = sessionManager.get_tool_schemas()
        function_names = [schema["function"]["name"] for schema in schemas]
        print(function_names)
        clusters = await sessionManager.session_tool_call("clusters", {})
        print(clusters.content[0].text)


async def manual_async_context():
    session_manager = MCPServerManager(sys.argv[1])  # Instantiate

    try:
        await session_manager.__aenter__()  # Manually enter the async context

        schemas = session_manager.get_tool_schemas()
        function_names = [schema["function"]["name"] for schema in schemas]
        print(function_names)

        clusters = await session_manager.session_tool_call("clusters", {})
        print(clusters.content[0].text)

    finally:
        await session_manager.__aexit__(None, None, None)  # Ensure cleanup


from contextlib import asynccontextmanager
from typing import AsyncGenerator


@asynccontextmanager
async def managed_session(config: str) -> AsyncGenerator[MCPServerManager, None]:
    session_manager = MCPServerManager(config)
    await session_manager.__aenter__()
    try:
        yield session_manager
    finally:
        await session_manager.__aexit__(None, None, None)


# reusability
async def with_decorator():
    async with managed_session(sys.argv[1]) as session_manager:
        schemas = session_manager.get_tool_schemas()
        print([schema["function"]["name"] for schema in schemas])
        print((await session_manager.session_tool_call("clusters", {})).content[0].text)


from contextlib import AsyncExitStack


# use for managing multiple async resources
async def with_exit_stack():
    async with AsyncExitStack() as stack:
        session_manager = await stack.enter_async_context(MCPServerManager(sys.argv[1]))

        schemas = session_manager.get_tool_schemas()
        print([schema["function"]["name"] for schema in schemas])

        clusters = await session_manager.session_tool_call("clusters", {})
        print(clusters.content[0].text)


async def explicit_exit_stack():
    stack = AsyncExitStack()  # Create exit stack
    await stack.__aenter__()  # Manually enter the async context

    try:
        session_manager = await stack.enter_async_context(MCPServerManager(sys.argv[1]))

        schemas = session_manager.get_tool_schemas()
        print([schema["function"]["name"] for schema in schemas])

        clusters = await session_manager.session_tool_call("clusters", {})
        print(clusters.content[0].text)

    finally:
        await stack.aclose()  # Ensure all contexts are properly closed


if __name__ == "__main__":
    asyncio.run(explicit_exit_stack())
