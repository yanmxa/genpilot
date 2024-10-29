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

console = rich.get_console()


class PromptAgent(Agent):

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

        self._tools: List[ChatCompletionToolParam] = []  # Placeholder

        # 1. render the prompt_agent to _system(time, name, system)
        # 2. append the tools to the _system
        self._system = self._build_system(
            os.path.join(current_dir, "..", "prompt", "prompt_agent.md"),
            {
                "{{name}}": self.name,
                "{{system}}": self.system,
            },
        )
        self._system += self._tool_markdown(tools)
        self.console.system(self._system)

    def _tool_markdown(self, tools) -> str:
        system_tool_content = ["## Available Tools:\n"]
        for tool in tools:
            func_name, func_args, func_desc = func_metadata(tool)
            tool_md = f"### {func_name}\n"
            tool_md += f"**Parameters**: {', '.join(func_args)}\n\n"
            tool_md += f"**Description**: {func_desc}\n"
            system_tool_content.append(tool_md)
        if len(tools) == 0:
            system_tool_content.append("### No tools are available")
        return "\n".join(system_tool_content)

    def run(self, message: Union[ChatCompletionMessageParam, str]):
        self._add_user_message(message)
        assistant_message = self._thinking()
        obs_status, obs_result = self._action_observation(assistant_message)
        i = 0
        while i < self._max_iter:
            if obs_status == StatusCode.ANSWER:
                next_input = self.console.answer(obs_result)
                if next_input:
                    self._add_user_message(next_input)
                    i = 0  # Reset iteration count for new input -> next
                else:
                    break
            elif obs_status == StatusCode.THOUGHT:  # -> next
                next_step = self.console.thought(obs_result)  # request the user prompt
                if next_step:
                    self._add_user_message(next_step)
            elif obs_status == StatusCode.OBSERVATION:  # -> next
                print()
            elif obs_status == StatusCode.ACTION_FORBIDDEN:
                return
            else:  # StatusCode.ERROR, StatusCode.NONE, StatusCode.ACTION_FORBIDDEN
                self.console.error(obs_result)
                return
            assistant_message = self._thinking()
            obs_status, obs_result = self._action_observation(assistant_message)
            i += 1
        if i == self._max_iter:
            self.console.overload(self._max_iter)

    def _thinking(self) -> ChatCompletionMessage:
        messages = self._add_system_messages(self._memory.get())
        self.console.thinking(messages)
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
        try:
            decoder = json.JSONDecoder()
            content = chat_message.content
            json_content, _ = decoder.raw_decode(content.strip())

            chat_message = ChatMessage.model_validate(json_content)

            if chat_message.thought:
                rich.get_console().print()
                rich.get_console().print("\n".join(chat_message.thought))
                rich.get_console().print()
            if chat_message.action:
                func_name = chat_message.action.name
                func_args = chat_message.action.args
                func_edit = chat_message.action.edit
                # validate the tool
                if not func_name in self._func_modules:
                    return (
                        StatusCode.ERROR,
                        f"The function [yellow]{func_name}[/yellow] isn't registered!",
                    )

                # validate the permission
                if not self.console.check_action(
                    self.permission, func_name, func_args, func_edit=func_edit
                ):
                    return StatusCode.ACTION_FORBIDDEN, "Action cancelled by the user."

                # observation
                module_name = self._func_modules[func_name]
                if module_name not in globals():
                    globals()[module_name] = importlib.import_module(module_name)
                func = getattr(sys.modules[module_name], func_name)
                observation = func(**func_args)

                self.console.observation(observation)

                self._memory.add(
                    self.console.check_observation(
                        ChatCompletionUserMessageParam(
                            role="user", content=f"{observation}"
                        ),
                        self._max_obs,
                    )
                )
                return StatusCode.OBSERVATION, f"{observation}"
            elif chat_message.answer:
                return StatusCode.ANSWER, chat_message.answer
            elif chat_message.thought:
                return StatusCode.THOUGHT, "\n".join(chat_message.thought)
            else:
                return (
                    StatusCode.NONE,
                    f"can't parse validate action, thought, or answer from the response",
                )
        except ValidationError as e:
            self._memory.add(
                ChatCompletionUserMessageParam(
                    content=f"Validate error in the response: {e}",
                    role="user",
                )
            )
            return (
                StatusCode.OBSERVATION,
                f"{content}\n Validate error, Should only contain the JSON object:\n {e}",
            )
        except Exception as e:
            return StatusCode.ERROR, f"{content}\n An structured error occurred: {e}"
