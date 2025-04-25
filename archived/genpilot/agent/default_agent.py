import json
from typing import Callable, List, Dict, Union
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCall,
)
import genpilot as gp
from genpilot.abc.agent import (
    ActionPermission,
    ActionType,
    Attribute,
    final_answer,
    ModelConfig,
)
from genpilot.utils.function_to_schema import func_to_param, function_to_schema
from genpilot.utils.mcp_server_config import AppConfig, McpServerConfig
from genpilot.tools.mcp_toolkit import McpToolkit
from ..abc.agent import IAgent
from ..abc.memory import IMemory
from ..abc.chat import IChat
from rich.console import Console
from rich.table import Table

from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


class Agent(IAgent):

    def __init__(
        self,
        name,
        system,
        tools: List[callable] = None,
        handoffs: List[IAgent] = [],
        memory: IMemory = None,
        chat: IChat = None,
        description: str = "",
        model_config: ModelConfig = None,
        # TODO: consider introduce terminate condition with autogen 4.0
        max_iter: str = 6,
        mcp_server_config: str = "",
        action_permission: ActionPermission = ActionPermission.ALWAYS,
        human_on_loop: bool = True,
        terminal_func: Callable = final_answer,
    ):
        self._attribute = Attribute(
            name,
            model_name=model_config["name"],
            model_config=model_config["config"],
            description=description or system,
            permission=action_permission,
            human_on_loop=human_on_loop,
        )
        self.chat = chat

        if not tools:
            tools = []

        # tools.append(final_answer)
        if terminal_func:
            tools.append(terminal_func)
        self.functions, self.function_schemas = self.register_function_tools(tools)
        self.agents, self.agent_schemas = self.register_agent_tools(handoffs)

        self.toolkits: Dict[str, McpToolkit] = {}
        self.toolkits_schemas = []

        # TODO: give a default chat console
        self._attribute.memory = (
            memory if memory is not None else gp.memory.BufferMemory(size=10)
        )
        self._attribute.memory.add(
            ChatCompletionSystemMessageParam(content=system, role="system", name=name)
        )

        self._max_iter = max_iter
        self.mcp_server_config = mcp_server_config
        self.exit_stack = AsyncExitStack()

    @property
    def attribute(self) -> Attribute:
        return self._attribute

    async def chatbot(self):
        print()
        while True:
            if not (await self()):
                break

    async def __call__(
        self,
        message: Union[ChatCompletionMessageParam, str] = None,
    ) -> ChatCompletionAssistantMessageParam | str | None:

        # 1. update memory: if the message is None, don't need add to the memory
        if not self.chat.input(self, message):
            return None

        i = 0
        while i == 0 or i < self._max_iter:
            # 2. reasoning -> return none indicate try again
            tool_schemas = (
                self.function_schemas + self.agent_schemas + self.toolkits_schemas
            )
            assistant_message: ChatCompletionAssistantMessageParam = (
                await self.chat.reasoning(agent=self, tool_schemas=tool_schemas)
            )

            if assistant_message is None:
                # input return false, means exiting
                if not self.chat.input(self, message):
                    self._attribute.memory.clear()
                    return None
                continue
            assistant_message["name"] = self._attribute.name
            self._attribute.memory.add(assistant_message)

            # if not contains the tool call, return the message as result
            if (
                "tool_calls" not in assistant_message
                or assistant_message["tool_calls"] is None
            ):
                # self._attribute.memory.clear()
                return assistant_message

            # 3. acting
            for tool_call in assistant_message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = tool_call["function"]["arguments"]
                tool_call_id = tool_call["id"]
                if isinstance(func_args, str):
                    func_args = json.loads(func_args)

                # validate
                action_type = ActionType.NONE
                if func_name in self.functions:
                    action_type = ActionType.FUNCTION
                if func_name in self.agents:
                    action_type = ActionType.AGENT
                if func_name in self.toolkits:
                    action_type = ActionType.SERVER

                if action_type == ActionType.NONE:
                    raise ValueError(f"The '{func_name}' isn't registered!")

                func_result = await self.chat.acting(
                    self, action_type, func_name, func_args
                )

                # add tool call result
                self._attribute.memory.add(
                    ChatCompletionToolMessageParam(
                        tool_call_id=tool_call_id,
                        # tool_name=tool_call.function.name, # tool name is not supported by groq client now
                        content=f"{func_result}",
                        role="tool",
                        name=func_name,
                    )
                )

            i += 1
        if i >= self._max_iter:
            self._attribute.memory.clear()
            return f"Reached maximum iterations: {self._max_iter}!"

    async def tool_call(self, func_name, func_args) -> str:
        func_result = ""

        # agent
        if func_name in self.agents:
            agent_task = ChatCompletionAssistantMessageParam(
                role="assistant",
                content=func_args["task"],
                name=self._attribute.name,
            )

            agent: IAgent = self.agents[func_name]
            agent_result = await agent(agent_task)
            if not agent_result:
                raise ValueError(f"{func_name} return None!")
            if isinstance(agent_result, str):
                raise ValueError(f"{func_name} return error: {agent_result}")

            func_result = agent_result["content"]

        # function
        if func_name in self.functions:
            func = self.functions[func_name]
            func_result = func(**func_args)

        # servers: TODO: add print message
        if func_name in self.toolkits:

            client_session: ClientSession = self.toolkits[func_name].session
            func_result: types.CallToolResult = await client_session.call_tool(
                func_name, func_args
            )
            if func_result.isError:
                raise ValueError(
                    f"tool call {func_name} return err {func_result.content}"
                )
            func_result = func_result.content

        if not func_result:
            raise ValueError(f"tool call {func_name} return none")
        return func_result

    def register_function_tools(self, tools):
        """
        Registers external tools by mapping their names to corresponding functions
        and generating structured chat tool parameters for each tool.

        Args:
            tools (List[Callable]): List of tool functions to register.

        Returns:
            dict: A mapping of tool names to their functions.
            dict: A mapping of tool names to their structured chat tool parameters.
        """
        # Register external functions (modules) to the agent
        # Reference: https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py#L251
        function_map = {tool.__name__: tool for tool in tools}
        function_schemas = [function_to_schema(tool) for tool in tools]
        return function_map, function_schemas

    def register_agent_tools(self, agents: List[IAgent]):
        def convert_agent_name(agent_name: str) -> str:
            agent_name = agent_name.strip().lower()
            agent_name = agent_name.replace(" ", "_")
            return f"transfer_to_{agent_name}"

        def agent_to_schema(agent: IAgent):
            description = agent.attribute.description.strip()
            return {
                "type": "function",
                "function": {
                    "name": convert_agent_name(agent.attribute.name),
                    "description": f"Hello, I am {agent.attribute.name}, here to assist you. {description}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "string",
                            },
                        },
                        "required": ["task"],
                    },
                },
            }

        function_map = {
            convert_agent_name(agent.attribute.name): agent for agent in agents
        }
        function_schemas = [agent_to_schema(agent) for agent in agents]

        return function_map, function_schemas

    async def connect_to_mcp_server(self, reconnect: bool = False):
        """Connect to an MCP server
        mount the session, stdio, write into the agent property
        """
        app_config: AppConfig = AppConfig.load(self.mcp_server_config)
        server_configs: List[McpServerConfig] = app_config.get_mcp_configs()

        toolkits: Dict[str, McpToolkit] = {}
        schemas = []

        async def convert_toolkit(server_config: McpServerConfig):
            server_param = server_config.server_param
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_param)
            )
            read, write = stdio_transport
            client_session: ClientSession = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await client_session.initialize()

            # list available tools
            tools_result: types.ListToolsResult = await client_session.list_tools()
            toolkit = McpToolkit(
                name=server_config.server_name,
                server_param=server_param,
                exclude_tools=server_config.exclude_tools,
                session=client_session,
                tools=tools_result.tools,
            )
            toolkits.update({tool.name: toolkit for tool in tools_result.tools})
            schemas.extend(toolkit.tool_schemas)

            # await client_session.list_resources()

        # TODO: consider run it the same time
        for server_param in server_configs:
            await convert_toolkit(server_param)

        self.toolkits = toolkits
        self.toolkits_schemas = schemas

        if reconnect:
            return

        console = Console()
        table = Table(title="Available MCP Server Tools")
        table.add_column("Toolkit", style="cyan")
        table.add_column("Tool Name", style="cyan")
        table.add_column("Description", style="green")

        seen_tools = set()

        for toolkit in self.toolkits.values():
            for tool in toolkit.tools:
                key = (toolkit.name, tool.name)
                # If the key hasn't been seen before, add it to the table and the set
                if key not in seen_tools:
                    table.add_row(toolkit.name, tool.name, tool.description)
                    # table.add_row(toolkit["name"], tool["name"], tool["description"])
                    seen_tools.add(key)
        print()
        console.print(table)
        # print()

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
