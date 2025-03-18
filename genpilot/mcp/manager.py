from typing import Dict, List, Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, types
from mcp.client.stdio import stdio_client
from genpilot.mcp.config import AppConfig, McpServerConfig
from genpilot.mcp.session import McpSessionKit
from rich.console import Console
from rich.table import Table


class MCPServerManager:
    def __init__(self, config_path: str, includes=None):
        """init the mcp server by the config file

        Args:
            config_path (str): json config file
            includes (_type_, optional): include mcp servers. Defaults to None.
        """
        self.session_kits: List[McpSessionKit] = []
        self.exit_stack = AsyncExitStack()  # Single exit stack to manage all sessions
        self.config_path = config_path
        self.includes: List[str] = includes  # includes servers

    async def __aenter__(self):
        await self.exit_stack.__aenter__()  # Enter exit stack context
        await self.connect_to_server(self.config_path)
        await self.list_tools()
        self._display_available_tools()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit_stack.__aexit__(
            exc_type, exc, tb
        )  # Exit all registered sessions

    def get_session_kit(self, tool_name: str) -> Optional[McpSessionKit]:
        """Retrieve the session kit associated with a given tool name."""
        return next(
            (
                kit
                for kit in self.session_kits
                if any(tool.name == tool_name for tool in kit.tools)
            ),
            None,
        )

    def get_tool_schemas(self) -> List[dict]:
        """Retrieve all tool schemas from available session kits."""
        return [
            schema for kit in self.session_kits for schema in kit.build_tool_schemas()
        ]

    async def session_tool_call(
        self, tool_name: str, tool_args: dict
    ) -> Optional[types.CallToolResult]:
        """Call a tool from the corresponding session kit."""
        session_kit = self.get_session_kit(tool_name)
        if not session_kit:
            return None  # Tool not found

        return await session_kit.session.call_tool(tool_name, tool_args)

    async def connect_to_server(self, mcp_server_config: str):
        """Connect to an MCP server and initialize session kits."""
        if not mcp_server_config:
            raise ValueError("Server config not set")

        app_config = AppConfig.load(mcp_server_config)
        server_params_configs = app_config.get_mcp_configs()

        # Initialize session kits using exit stack
        session_kits = []
        for server_config in server_params_configs:
            if self.includes and server_config.server_name not in self.includes:
                continue
            kit = await self._convert_kit(server_config)
            session_kits.append(kit)

        self.session_kits = session_kits

    async def _convert_kit(self, server_config: McpServerConfig) -> McpSessionKit:
        """Initialize a session kit for a given MCP server configuration."""
        read, write = await self.exit_stack.enter_async_context(
            stdio_client(server_config.server_params)
        )
        client_session: ClientSession = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )

        await client_session.initialize()

        return McpSessionKit(
            name=server_config.server_name,
            server_param=server_config.server_params,
            exclude_tools=server_config.exclude_tools,
            session=client_session,
        )

    async def list_tools(self) -> List[types.Tool]:
        tools = []
        for session_kit in self.session_kits:
            client_session = session_kit.session
            tools_result = await client_session.list_tools()
            session_kit.tools = tools_result.tools
            tools.extend(tools)
        return tools

    def _display_available_tools(self):
        """Display available MCP tools in a formatted table."""
        console = Console()
        table = Table(title="Available MCP Server Tools")
        table.add_column("Session Kit", style="cyan")
        table.add_column("Tool Name", style="cyan")
        table.add_column("Description", style="green")

        seen_tools = set()
        for kit in self.session_kits:
            for tool in kit.tools:
                key = (kit.name, tool.name)
                if key not in seen_tools:
                    table.add_row(kit.name, tool.name, tool.description)
                    seen_tools.add(key)

        console.print(table)
