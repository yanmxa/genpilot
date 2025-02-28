from dataclasses import dataclass
from pathlib import Path
import os
import commentjson
from typing import Dict, List, Optional
from mcp import StdioServerParameters, types, ClientSession
from pydantic import BaseModel


class McpServerConfig(BaseModel):
    """Configuration for an MCP server.

    This class represents the configuration needed to connect to and identify an MCP server,
    containing both the server's name and its connection parameters.

    Attributes:
        server_name (str): The name identifier for this MCP server
        server_param (StdioServerParameters): Connection parameters for the server, including
            command, arguments and environment variables
        exclude_tools (list[str]): List of tool names to exclude from this server
    """

    server_name: str
    server_param: StdioServerParameters
    exclude_tools: list[str] = []


@dataclass
class ServerConfig:
    """Configuration for an MCP server."""

    command: str
    args: List[str] = None
    env: Dict[str, str] = None
    enabled: bool = True
    exclude_tools: List[str] = None
    requires_confirmation: List[str] = None

    @classmethod
    def from_dict(cls, config: dict) -> "ServerConfig":
        """Create ServerConfig from dictionary."""
        return cls(
            command=config["command"],
            args=config.get("args", []),
            env=config.get("env", {}),
            enabled=config.get("enabled", True),
            exclude_tools=config.get("exclude_tools", []),
            requires_confirmation=config.get("requires_confirmation", []),
        )


@dataclass
class AppConfig:
    """Main application configuration."""

    mcp_servers: Dict[str, ServerConfig]
    tools_requires_confirmation: List[str]

    @classmethod
    def load(cls, config_path) -> "AppConfig":
        """Load configuration from file."""
        if config_path is None:
            raise FileNotFoundError(
                f"Could not find config file in any of: {', '.join(map(str, config_path))}"
            )

        with open(config_path, "r") as f:
            config = commentjson.load(f)

        # Extract tools requiring confirmation
        tools_requires_confirmation = []
        for server_config in config["mcpServers"].values():
            tools_requires_confirmation.extend(
                server_config.get("requires_confirmation", [])
            )

        return cls(
            mcp_servers={
                name: ServerConfig.from_dict(server_config)
                for name, server_config in config["mcpServers"].items()
            },
            tools_requires_confirmation=tools_requires_confirmation,
        )

    def get_enabled_servers(self) -> Dict[str, ServerConfig]:
        return {
            name: config for name, config in self.mcp_servers.items() if config.enabled
        }

    def get_mcp_configs(self) -> List[McpServerConfig]:
        return [
            McpServerConfig(
                server_name=name,
                server_param=StdioServerParameters(
                    command=config.command,
                    args=config.args or [],
                    env={**(config.env or {}), **os.environ},
                ),
                exclude_tools=config.exclude_tools or [],
            )
            for name, config in self.get_enabled_servers().items()
        ]
