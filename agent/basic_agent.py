from typing import Union, Tuple, List
import os
import sys
import json

from pydantic import ValidationError

import importlib
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
)
import rich
from rich.markdown import Markdown
from type import ChatMessage, StatusCode
import json

from tool import (
    Permission,
    chat_tool,
    tool_name,
    func_metadata,
)
from memory import ChatMemory, ChatBufferedMemory
from .console_agent import ConsoleAgent
from .agent import Agent


current_dir = os.path.dirname(os.path.realpath(__file__))
FINAL_ANSWER = "ANSWER:"

console = rich.get_console()


class DefaultAgent(Agent):

    def __init__(
        self,
        client,
        name,
        system,
        tools=[],
        memory: ChatMemory = None,
        permission=Permission.ALWAYS,
    ):
        self.client = client
        self.name = name
        self.system = system
        self.tools = tools
        self.permission = permission
        if memory is None:
            self._memory = ChatBufferedMemory(name, 5)
        self.console = ConsoleAgent(name)

        self._max_iter = 6
        self._max_obs = 200  # max observation word size!

        # register the external func(modules) to the agent
        self._func_modules = {}
        for tool in tools:
            func_name, func_module = tool_name(tool)
            self._func_modules[func_name] = func_module

        # 1. generate the _tools from tools: https://platform.openai.com/docs/guides/function-calling
        # 2. render the basic_agent to _system(time, name, system, FINAL_ANSWER)
        self._tools: List[ChatCompletionToolParam] = self._chat_completion_tools(tools)
        self._system = self._build_system(
            "basic_agent.md",
            {
                "{{name}}": self.name,
                "{{system}}": self.system,
                "{{FINAL_ANSWER}}": FINAL_ANSWER,
            },
        )

        console.print(Markdown(self._system))

        self.chat_system_message = ChatCompletionSystemMessageParam(
            role="system",
            content=self._system,
        )

    def run(self, message: Union[ChatCompletionMessageParam, str]):
        self._add_user_message(message)
        assistant_message = self._thinking()
        obs_status, obs_result = self._action_observation(assistant_message)
        i = 0
        while i < self._max_iter:
            if obs_status == StatusCode.ANSWER:
                next_input = self.console.answer(obs_result)
                if next_input:
                    self._add_user_message(input)
                    i = 0  # Reset iteration count for new input -> next
                else:
                    break
            elif obs_status == StatusCode.THOUGHT:  # -> next
                print()  # TODO: add the thought, might be need add user prompt
            elif obs_status == StatusCode.OBSERVATION:  # -> next
                print()
            else:  # StatusCode.ERROR, StatusCode.NONE, StatusCode.ACTION_FORBIDDEN
                self.console.error(obs_result)
                return
            assistant_message = self._thinking()
            obs_status, obs_result = self._action_observation(assistant_message)
            i += 1
        if i == self._max_iter:
            self.console.overload(self._max_iter)

    def _thinking(self) -> ChatCompletionMessage:
        messages = self._memory.get()
        messages.insert(0, self.chat_system_message)

        self.console.thinking()
        assistant_chat_message: ChatCompletionMessage = self.client(
            messages, self._tools
        )
        self._memory.add(assistant_chat_message)
        return assistant_chat_message

    # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_message_param.py
    # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_tool_param.py
    # https://platform.openai.com/docs/guides/function-calling

    def _add_user_message(self, message: Union[ChatCompletionUserMessageParam, str]):
        if isinstance(message, str):
            message = ChatCompletionUserMessageParam(content=message, role="user")
        self._memory.add(message)

    def _action_observation(
        self, chat_message: ChatCompletionMessage
    ) -> Tuple[StatusCode, str]:
        if chat_message.tool_calls:
            tool = chat_message.tool_calls[0]
            func_name = tool.function.name
            func_args = tool.function.arguments
            if isinstance(func_args, str):
                func_args = json.loads(tool.function.arguments)
            func_tool_call_id = tool.id

            # validate the tool
            if not func_name in self._func_modules:
                return (
                    StatusCode.ERROR,
                    f"The [yellow]{func_name}[/yellow] isn't registered!",
                )

            # call tool: not all -> exit
            if not self.console.check_action(func_name, func_args):
                return StatusCode.ACTION_FORBIDDEN, "Action cancelled by the user."

            # invoke function
            func_module = self._func_modules[func_name]
            if func_module not in globals():
                globals()[func_module] = importlib.import_module(func_module)
            func_tool = getattr(sys.modules[func_module], func_name)
            observation = func_tool(**func_args)

            self.console.observation(observation)

            # append the tool response: observation
            self._memory.add(
                self.console.check_observation(
                    ChatCompletionToolMessageParam(
                        tool_call_id=func_tool_call_id,
                        content=f"{observation}",
                        role="tool",
                    ),
                    self._max_obs,
                )
            )
            return StatusCode.OBSERVATION, observation
        elif chat_message.content:
            if chat_message.content.startswith(FINAL_ANSWER):
                return (
                    StatusCode.ANSWER,
                    chat_message.content.removeprefix(FINAL_ANSWER),
                )
            else:
                return (StatusCode.THOUGHT, chat_message.content)
        else:
            return (
                StatusCode.NONE,
                f"Invalid response message: {chat_message}",
            )

    def _chat_completion_tools(self, tools):
        func_tools = []
        for tool in tools:
            # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py#L251
            _, _, chat_completion_tool = chat_tool(tool)
            func_tools.append(chat_completion_tool)
        return func_tools
