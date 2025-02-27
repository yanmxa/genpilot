from pydantic import BaseModel, model_validator
from mcp import StdioServerParameters, types, ClientSession
from typing import Optional, List


class McpToolkit(BaseModel):
    name: str
    server_param: StdioServerParameters
    exclude_tools: list[str] = []
    session: Optional[ClientSession] = None
    tools: List[types.Tool] = []
    tool_schemas: List[dict] = []

    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types like ClientSession

    @model_validator(mode="before")
    def build_tool_schemas(cls, values):
        tools = values.get("tools", [])
        tool_schemas = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools
        ]
        values["tool_schemas"] = tool_schemas
        return values
