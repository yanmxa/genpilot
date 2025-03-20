import json
from pydantic import BaseModel
from mcp import StdioServerParameters, types, ClientSession, Tool
from typing import Optional, List, Any, Dict, Callable
from agents.tool import FunctionTool
from agents.run_context import RunContextWrapper


class MCPServer(BaseModel):
    name: str
    server_params: StdioServerParameters
    exclude_tools: list[str] = []
    client_session: Optional[ClientSession] = None

    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types like ClientSession

    # Deprecated
    def _build_tool_schemas(self) -> List[dict]:
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

    async def function_tools(
        self, tool_validators: Dict[str, Callable[[dict], str]]
    ) -> List[FunctionTool]:
        """Convert MCP tools into agent SDK tools."""

        tools_result = await self.client_session.list_tools()

        async def on_invoke_tool(
            ctx: RunContextWrapper[Any], parameters: str, tool_name: str
        ) -> str:
            """Handles tool invocation with JSON parsing."""
            params = (
                json.loads(parameters) if isinstance(parameters, str) else parameters
            )
            # human in loop
            tool_validator = tool_validators[tool_name]
            if tool_validator:
                result = tool_validator(
                    params
                )  # if result exist, then return the result, else go on
                if result:
                    return result

            # add access control in here
            result: types.CallToolResult = await self.client_session.call_tool(
                tool_name, params
            )
            if result.isError:
                return "".join(c.text for c in result.content)
            return str(result)

        return [
            FunctionTool(
                name=tool.name,
                description=tool.description,
                params_json_schema=tool.inputSchema,
                on_invoke_tool=lambda ctx, params, tool_name=tool.name: on_invoke_tool(
                    ctx, params, tool_name
                ),
                strict_json_schema=False,
            )
            for tool in tools_result.tools
            if tool.name not in self.exclude_tools
        ]
