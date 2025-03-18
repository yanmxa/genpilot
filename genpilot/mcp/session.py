from pydantic import BaseModel, model_validator
from mcp import StdioServerParameters, types, ClientSession
from typing import Optional, List
from contextlib import AsyncExitStack


class McpSessionKit(BaseModel):
    name: str
    server_param: StdioServerParameters
    session: Optional[ClientSession] = None
    tools: List[types.Tool] = []
    exclude_tools: list[str] = []

    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types like ClientSession

    def build_tool_schemas(self) -> List[dict]:
        tool_schemas = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in self.tools
            if tool.name not in self.exclude_tools
        ]
        return tool_schemas
