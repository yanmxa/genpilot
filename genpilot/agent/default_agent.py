import os
import json
import sys
from typing import Union, Tuple, List, Protocol, List
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
from genpilot.abc.agent import ActionType, Attribute
from genpilot.utils.function_to_schema import func_to_param, function_to_schema
from tools.metadata import tool_name
from ..abc.agent import IAgent
from ..abc.memory import IMemory
from ..abc.chat import IChat

import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class Agent(IAgent):

    def __init__(
        self,
        name,
        system,
        tools=[],
        handoffs=[],
        memory: IMemory = None,
        chat: IChat = None,
        description="",
        model_name="",
        model_config={},
        # TODO: consider introduce terminate condition with autogen 4.0
        max_iter=6,
    ):
        self._attribute = Attribute(
            name,
            model_name=model_name,
            model_config=model_config,
            description=description or system,
        )
        self.chat = chat

        self.functions, self.function_schemas = self.register_function_tools(tools)
        self.agents, self.agent_schemas = self.register_agent_tools(handoffs)
        self.servers, self.server_schemas = {}, []

        # TODO: give a default chat console
        self._attribute.memory = (
            memory if memory is not None else gp.memory.BufferMemory(size=10)
        )
        self._attribute.memory.add(
            ChatCompletionSystemMessageParam(content=system, role="system", name=name)
        )

        self._max_iter = max_iter
        self.exit_stack = AsyncExitStack()

    @property
    def attribute(self) -> Attribute:
        return self._attribute

    async def chatbot(self):
        while True:
            if not (await self()):
                break

    async def __call__(
        self,
        message: Union[ChatCompletionMessageParam, str] = None,
    ) -> ChatCompletionAssistantMessageParam | str | None:

        # 1. update memory: if the message is None, don't need add to the memory
        if not self.chat.input(self, message):
            print("input none")
            return None

        i = 0
        while i == 0 or i < self._max_iter:
            # 2. reasoning -> return none indicate try again
            tool_schemas = (
                self.function_schemas + self.agent_schemas + self.server_schemas
            )
            assistant_message: ChatCompletionAssistantMessageParam = (
                await self.chat.reasoning(agent=self, tool_schemas=tool_schemas)
            )
            if assistant_message is None:
                print("assistant return none")
                return None

            if (
                "tool_calls" not in assistant_message
                or assistant_message["tool_calls"] is None
            ):
                self._attribute.memory.clear()
                i = 0
                return assistant_message

            assistant_message["name"] = self._attribute.name

            self._attribute.memory.add(assistant_message)

            # 3. actioning
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
                if func_name in self.servers:
                    action_type = ActionType.SEVER

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
            self.memory.clear()
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
        if func_name in self.servers:
            session_tool_call = self.servers[func_name]
            func_result = await session_tool_call(func_name, func_args)

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
                            "task": "string",
                            "description": "The task you want the agent to perform",
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

    async def register_server_tools(self, server_script_path: str):
        """Connect to an MCP server
        mount the session, stdio, write into the agent property

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        # init session in here
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()

        print(
            "\nConnected to server with tools:", [tool.name for tool in response.tools]
        )
        print()

        self.servers = {tool.name: self.session.call_tool for tool in response.tools}

        self.server_schemas = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in response.tools
        ]

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
