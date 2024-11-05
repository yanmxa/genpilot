import os
import sys
import json
import importlib
import rich
from typing import Union, Tuple, List
from pydantic import ValidationError
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
)
from type import ChatMessage, StatusCode
from tool import func_metadata, build_from_template
from .agent import Agent
import traceback
from memory.chat_buffer_memory import ChatBufferMemory


current_dir = os.path.dirname(os.path.realpath(__file__))

console = rich.get_console()


class PromptAgent(Agent):

    def __init__(self, client, name, system, tools=[], max_iter=6, memory=None):
        system = build_from_template(
            os.path.join(current_dir, "..", "prompt", "prompt_agent.md"),
            {
                "{{name}}": name,
                "{{system}}": system,
            },
        )
        system += self._tool_markdown(tools)
        super().__init__(name, system, tools, client, max_iter=max_iter, memory=memory)

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

    # override the abc, let the tools provided by system
    def completion_chat_tools(self, tools) -> List[ChatCompletionToolParam]:
        return []

    # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_message_param.py
    # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_tool_param.py
    # https://platform.openai.com/docs/guides/function-calling

    async def _action_observation(
        self, chat_message: ChatCompletionMessage
    ) -> Tuple[StatusCode, str]:
        try:
            decoder = json.JSONDecoder()
            content = chat_message.content
            json_content, _ = decoder.raw_decode(content.strip())

            chat_message: ChatMessage = ChatMessage.model_validate(json_content)

            if chat_message.thought:
                rich.get_console().print()
                rich.get_console().print("\n".join(chat_message.thought))
                rich.get_console().print()
            if chat_message.action:
                func_name = chat_message.action.name
                func_args = chat_message.action.args
                func_edit = chat_message.action.edit
                # validate the tool
                if not func_name in self._functions:
                    return (
                        StatusCode.ERROR,
                        f"The function [yellow]{func_name}[/yellow] isn't registered!",
                    )

                # validate the permission
                if not self._console.check_action(
                    self._action_permission, func_name, func_args, func_edit=func_edit
                ):
                    return StatusCode.ACTION_FORBIDDEN, "Action cancelled by the user."

                status, observation = await self._observation(func_name, func_args)
                if status == StatusCode.ERROR:
                    return StatusCode.ERROR, observation

                if observation == "":
                    observation = "no result found the action"

                self._memory.add(
                    self._console.check_observation(
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
            traceback.print_exc()
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
            traceback.print_exc()
            self._memory.add(
                ChatCompletionUserMessageParam(
                    content=f"Validate error in the response: {e}",
                    role="user",
                )
            )
            return (
                StatusCode.OBSERVATION,
                f"{content}\n An structured error occurred: {e}",
            )
