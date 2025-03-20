import typing
from typing import List, Callable, Dict
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from genpilot.mcp.config import AppConfig
from genpilot.mcp.server import MCPServer
from rich.console import Console
from rich.table import Table
import asyncio
import os


class MCPServerManager:
    def __init__(self, config_path: str, includes=None, display_tools=True):
        """init the mcp server by the config file

        Args:
            config_path (str): json config file
            includes (_type_, optional): include mcp servers. Defaults to None means all.
        """
        self.servers: List[MCPServer] = []
        self.exit_stack = AsyncExitStack()  # Single exit stack to manage all sessions
        self.config_path = config_path
        self.includes: List[str] = includes  # includes servers
        self.tool_validators: Dict[str, Callable[[dict], str]] = {}
        self.display_tools = display_tools

    async def __aenter__(self):
        await self.exit_stack.__aenter__()  # Enter exit stack context
        await self.connect_to_server(self.config_path)
        if self.display_tools:
            await self._display_available_tools()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit_stack.__aexit__(
            exc_type, exc, tb
        )  # Exit all registered sessions

    def register_validator(self, tool_name: str, tool_validator: Callable[[dict], str]):
        """
        Registers a validator function for a given tool.

        - `tool_name`: Name of the tool requiring validation.
        - `tool_validator`: A function that validates input parameters.
          Returns an empty string ("") to proceed or a non-empty string
          to provide an alternative Human tool result.
        """
        self.tool_validators[tool_name] = tool_validator

    async def function_tools(self):
        """Aggregates function tools from all server sessions sequentially."""
        function_tools = []

        for session in self.servers:
            tools = await session.function_tools(
                self.tool_validators
            )  # Await each session call one by one
            function_tools.extend(tools)

        return function_tools

    async def connect_to_server(self, mcp_server_config: str):
        """Connects to an MCP server and initializes session kits."""
        if not mcp_server_config:
            raise ValueError("Server config not set")

        app_config = AppConfig.load(mcp_server_config)

        mcp_servers = [
            MCPServer(
                name=name,
                server_params=StdioServerParameters(
                    command=config.command,
                    args=config.args or [],
                    env={**(config.env or {}), **os.environ},
                ),
                exclude_tools=config.exclude_tools or [],
            )
            for name, config in app_config.get_enabled_servers().items()
        ]

        self.servers = []
        for server in mcp_servers:
            if not self.includes or server.name in self.includes:
                await self._initialize_session(server)  # Await one by one
                self.servers.append(server)

    async def _initialize_session(self, mcp_server: MCPServer):
        """Initialize a session kit for a given MCP server configuration."""
        read, write = await self.exit_stack.enter_async_context(
            stdio_client(mcp_server.server_params)
        )
        client_session: ClientSession = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await client_session.initialize()
        mcp_server.client_session = client_session

    async def _display_available_tools(self):
        """Displays available MCP tools in a formatted table using parallel execution."""
        console = Console()
        table = Table(title="Available MCP Server Tools")

        table.add_column("Session Kit", style="cyan")
        table.add_column("Tool Name", style="cyan")
        table.add_column("Description", style="green")

        seen_tools = set()

        # Run function_tools() concurrently for all sessions
        results = await asyncio.gather(
            *(session.function_tools(self.tool_validators) for session in self.servers)
        )

        for session, tools in zip(self.servers, results):
            for tool in tools:
                key = (session.name, tool.name)
                if key not in seen_tools:
                    table.add_row(session.name, tool.name, tool.description)
                    seen_tools.add(key)

        console.print(table)
