from dataclasses import dataclass
from pathlib import Path
import os
import commentjson
from typing import Dict, List, Optional
from mcp import StdioServerParameters, types, ClientSession
from pydantic import BaseModel


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
