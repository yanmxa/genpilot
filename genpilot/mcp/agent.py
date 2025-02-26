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
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import genpilot as gp
from genpilot.chat.terminal_chat import TerminalChat
from genpilot.chat.chainlit_chat import rprint
from genpilot.abc.mcp_chat import MCPChat
from genpilot.abc.mcp_agent import MCPAgent
from ..abc.memory import IMemory
import traceback


class Agent(MCPAgent):

    def __init__(
        self,
        name,
        system,
        model="",
        chat: MCPChat = None,
        memory: IMemory = None,
    ):
        self._name = name
        self._model = model
        self._memory = memory if memory is not None else gp.memory.BufferMemory(size=10)
        self._memory.add(
            ChatCompletionSystemMessageParam(content=system, role="system", name=name)
        )
        self._chat: MCPChat = chat
        self._max_iter = 7
        self.exit_stack = AsyncExitStack()

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model

    @property
    def memory(self) -> IMemory:
        return self._memory

    @property
    def session(self):
        return self._session

    async def chatbot(self):
        while True:
            try:
                result = await self.run()
                if result is None:
                    break
                if isinstance(result, str):
                    rprint(f"error: {str}")
                    break
            except Exception as e:
                print(f"\nError: {str(e)}")
                traceback.print_exc()  # Print the full stack trace

    async def tools(self):
        session_response = await self._session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in session_response.tools
        ]
        return available_tools

    async def run(
        self,
        message: Union[ChatCompletionMessageParam, str, None] = None,
    ) -> ChatCompletionAssistantMessageParam | str | None:

        # 1. input message for user/assistant
        if not self._chat.input(self, message):
            self.memory.clear()
            return None

        i = 0
        while i == 0 or i < self._max_iter:
            # 2. reasoning -> return none indicate try again
            assistant_message: ChatCompletionAssistantMessageParam = (
                await self._chat.reasoning(agent=self)
            )
            if assistant_message is None:
                rprint(f"assistant({self.name}) return empty message")
                break

            if (
                "tool_calls" not in assistant_message
                or assistant_message["tool_calls"] is None
            ):
                self.memory.clear()
                i = 0
                return assistant_message

            # 3. actioning
            self.memory.add(assistant_message)
            for tool_call in assistant_message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = tool_call["function"]["arguments"]
                tool_call_id = tool_call["id"]
                if isinstance(func_args, str):
                    func_args = json.loads(func_args)
                # # validate
                # if not func_name in self.functions:
                #     raise ValueError(f"The '{func_name}' isn't registered!")

                # func = self.functions[func_name]
                # return_type = func.__annotations__.get("return")
                # # agent invoking
                # if return_type is not None and issubclass(return_type, IAgent):
                #     target_agent: IAgent = func(**func_args)
                #     target_message = ChatCompletionAssistantMessageParam(
                #         role="assistant", content=func_args["message"], name=self.name
                #     )
                #     target_response: ChatCompletionAssistantMessageParam = (
                #         target_agent.run(target_message)
                #     )
                #     if target_response is None:
                #         raise ValueError(
                #             f"The agent{target_agent.name} observation is None!"
                #         )
                #     if isinstance(target_response, str):
                #         raise ValueError(
                #             f"{target_agent.name} error: {target_response}"
                #         )
                #     content = target_response["content"]
                #     self.memory.add(
                #         ChatCompletionToolMessageParam(
                #             tool_call_id=tool_call_id,
                #             content=f"{content}",
                #             role="tool",
                #             name=func_name,
                #         )
                #     )
                # function invoking
                # else:
                func_result = await self._chat.acting(self, func_name, func_args)
                self.memory.add(
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

    async def connect_to_server(self, server_script_path: str):
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
        self.stdio, self.write = stdio_transport
        self._session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self._session.initialize()

        # List available tools
        response = await self._session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])
        print()

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
