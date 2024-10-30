import os
import sys
import json
import importlib

from abc import ABC, abstractmethod
from typing import Union, Tuple, List

from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
)

from tool import (
    chat_tool,
    tool_name,
)
from type import StatusCode, ActionPermission
from memory import ChatMemory, ChatBufferedMemory
from .chat_console import ChatConsole

current_dir = os.path.dirname(os.path.realpath(__file__))
FINAL_ANSWER = "ANSWER:"


class ChatAgent(ABC):

    def __init__(
        self,
        name,
        system,
        tools,
        client,
        standalone: bool = True,
        action_permission: ActionPermission = ActionPermission.ALWAYS,
        memory: ChatMemory = ChatBufferedMemory(5),
        chat_console: ChatConsole = ChatConsole(),
        max_iter=6,
        max_obs=200,  # max observation content!
    ):
        self.name = name
        self._client = client
        self._system = system
        # registered the tools for the agent to be invoked
        self._functions = self._register_tools(tools)
        # the tools for model
        self._tools: List[ChatCompletionToolParam] = self.completion_chat_tools(tools)

        self._standalone = standalone
        self._action_permission = action_permission
        self._memory = memory
        self._console = chat_console
        self._max_iter = max_iter
        self._max_obs = max_obs

        self._console.system(self._system)

    def _register_tools(self, tools):
        # register the external func(modules) to the agent
        functions = {}
        for tool in tools:
            func_name, func_module = tool_name(tool)
            functions[func_name] = func_module
        return functions

    def completion_chat_tools(self, tools) -> List[ChatCompletionToolParam]:
        # parse the tools to chat functions
        func_tools = []
        for tool in tools:
            # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py#L251
            _, _, chat_completion_tool = chat_tool(tool)
            func_tools.append(chat_completion_tool)
        return func_tools

    def _thinking(self) -> ChatCompletionMessage:
        new_messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=self._system,
            )
        ]
        memory_messages = self._memory.get()
        for message in memory_messages:
            new_messages.append(message)
        self._console.thinking(new_messages)
        assistant_message: ChatCompletionMessage = self._client(
            new_messages, self._tools
        )
        self._memory.add(assistant_message)
        return assistant_message

    def run(self, message: Union[ChatCompletionMessageParam, str]):
        self._add_user_message(message)
        assistant_message = self._thinking()
        obs_status, obs_result = self._action_observation(assistant_message)
        i = 0
        while i < self._max_iter:
            if obs_status == StatusCode.ANSWER:  # return, input or thinking
                self._console.answer(obs_result)
                if not self._standalone:
                    self._memory.clear()
                    return obs_result
                next_input = self._console.ask_input()
                if next_input:
                    self._add_user_message(next_input)
                    i = 0
                else:
                    return obs_result
            elif obs_status == StatusCode.THOUGHT:  # input or thinking
                self._console.thought(obs_result)
                next_step = self._console.ask_input()
                if next_step:
                    self._add_user_message(next_step)
                else:
                    return
            elif obs_status == StatusCode.OBSERVATION:  # thinking
                print()
            elif obs_status == StatusCode.ACTION_FORBIDDEN:  # return None
                return
            else:  # StatusCode.ERROR, StatusCode.NONE       # return None
                self._console.error(obs_result)
                return
            assistant_message = self._thinking()
            obs_status, obs_result = self._action_observation(assistant_message)
            i += 1
        if i == self._max_iter:
            self._console.overload(self._max_iter)

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
            if not func_name in self._functions:
                return (
                    StatusCode.ERROR,
                    f"The [yellow]{func_name}[/yellow] isn't registered!",
                )

            # call tool: not all -> exit
            if not self._console.check_action(
                self._action_permission, func_name, func_args
            ):
                return StatusCode.ACTION_FORBIDDEN, "Action cancelled by the user."

            # invoke function
            func_module = self._functions[func_name]
            if func_module not in globals():
                globals()[func_module] = importlib.import_module(func_module)
            func_tool = getattr(sys.modules[func_module], func_name)
            observation = func_tool(**func_args)

            self._console.observation(observation)

            # append the tool response: observation
            self._memory.add(
                self._console.check_observation(
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

    # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_message_param.py
    # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_tool_param.py
    # https://platform.openai.com/docs/guides/function-calling

    def _add_user_message(self, message: Union[ChatCompletionUserMessageParam, str]):
        if isinstance(message, str):
            message = ChatCompletionUserMessageParam(content=message, role="user")
        self._memory.add(message)
