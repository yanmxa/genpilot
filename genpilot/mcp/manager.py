from typing import List
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from genpilot.mcp.config import AppConfig, MCPServerConfig
from genpilot.mcp.server import MCPServerSession
from rich.console import Console
from rich.table import Table
import asyncio


class MCPServerManager:
    def __init__(self, config_path: str, includes=None):
        """init the mcp server by the config file

        Args:
            config_path (str): json config file
            includes (_type_, optional): include mcp servers. Defaults to None.
        """
        self.servers: List[MCPServerSession] = []
        self.exit_stack = AsyncExitStack()  # Single exit stack to manage all sessions
        self.config_path = config_path
        self.includes: List[str] = includes  # includes servers

    async def __aenter__(self):
        await self.exit_stack.__aenter__()  # Enter exit stack context
        await self.connect_to_server(self.config_path)
        # await self.list_tools()
        await self._display_available_tools()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit_stack.__aexit__(
            exc_type, exc, tb
        )  # Exit all registered sessions

    async def agent_function_tools(self):
        """Aggregates function tools from all server sessions sequentially."""
        function_tools = []

        for session in self.servers:
            tools = await session.function_tools()  # Await each session call one by one
            function_tools.extend(tools)

        return function_tools

    async def connect_to_server(self, mcp_server_config: str):
        """Connects to an MCP server and initializes session kits."""
        if not mcp_server_config:
            raise ValueError("Server config not set")

        app_config = AppConfig.load(mcp_server_config)
        server_configs = app_config.get_mcp_server_configs()

        self.servers = []
        for cfg in server_configs:
            if not self.includes or cfg.server_name in self.includes:
                session = await self._initialize_session(cfg)  # Await one by one
                self.servers.append(session)

    async def _initialize_session(
        self, server_config: MCPServerConfig
    ) -> MCPServerSession:
        """Initialize a session kit for a given MCP server configuration."""
        read, write = await self.exit_stack.enter_async_context(
            stdio_client(server_config.server_params)
        )
        client_session: ClientSession = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )

        await client_session.initialize()

        return MCPServerSession(
            name=server_config.server_name,
            server_params=server_config.server_params,
            exclude_tools=server_config.exclude_tools,
            client_session=client_session,
        )

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
            *(session.function_tools() for session in self.servers)
        )

        for session, tools in zip(self.servers, results):
            for tool in tools:
                key = (session.name, tool.name)
                if key not in seen_tools:
                    table.add_row(session.name, tool.name, tool.description)
                    seen_tools.add(key)

        console.print(table)
