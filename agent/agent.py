import os
import json
import asyncio

from typing import Union, Tuple, List, Protocol
from abc import ABC, abstractmethod

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

from tool import (
    chat_tool,
    tool_name,
)
from type import StatusCode, ActionPermission
from memory import ChatMemory, ChatBufferMemory
import instructor
from .interface import IAgent
from .chat import ChatConsole


current_dir = os.path.dirname(os.path.realpath(__file__))
FINAL_ANSWER = "ANSWER:"


class Agent(IAgent):

    def __init__(
        self,
        name,
        system,
        client,
        tools=[],
        action_permission: ActionPermission = ActionPermission.ALWAYS,
        memory: ChatMemory = None,
        chat_console=None,
        max_iter=6,
        max_obs=200,  # max observation content!
        is_terminal=(lambda content: content is not None and FINAL_ANSWER in content),
        response_model=None,
    ):
        self._name = name
        self._client = client
        self._system = system
        # registered the tools for the agent to be invoked
        self._functions = self.register_actions(tools)
        # the tools for model
        self._tools: List[ChatCompletionToolParam] = self.completion_chat_tools(tools)
        self._standalone = True
        self._action_permission = action_permission
        self._memory = (
            memory if memory is not None else ChatBufferMemory(memory_id=name, size=10)
        )
        self._console = chat_console if chat_console is not None else ChatConsole(name)
        self._max_iter = max_iter
        self._max_obs = max_obs
        self._is_terminal = is_terminal

        self._console.system(self._system)

        self._response_model = response_model

    @property
    def name(self):
        return self._name

    def messages(self) -> List[ChatCompletionMessageParam]:
        return self._memory.get(None)

    async def _thinking(self) -> ChatCompletionMessage:
        new_messages = self._memory.get(self._system)

        finished_event = asyncio.Event()
        model_thinking_task = asyncio.create_task(
            self.async_wrapper_client(new_messages, self._tools, self._response_model)
        )
        console_thinking_task = asyncio.create_task(
            self._console.async_thinking(new_messages, finished_event)
        )

        assistant_message, price = await model_thinking_task
        finished_event.set()
        await console_thinking_task
        self._console.price(price)

        assistant_param = ChatCompletionAssistantMessageParam(
            role="assistant",
            name=self.name,
        )
        if assistant_message.content is not None and assistant_message.content != "":
            assistant_param["content"] = assistant_message.content.replace(
                FINAL_ANSWER, ""
            ).strip()
        if assistant_message.function_call is not None:
            assistant_param["function_call"] = assistant_message.function_call
        if assistant_message.tool_calls is not None:
            assistant_param["tool_calls"] = assistant_message.tool_calls

        self._memory.add(assistant_param)
        return assistant_message

    async def run(
        self,
        message: Union[ChatCompletionMessageParam, str],
    ) -> ChatCompletionAssistantMessageParam | None:
        if not isinstance(message, str):
            self._standalone = False
        self._add_user_message(message)
        if not self._console.before_thinking(self._memory):
            return None
        assistant_message = await self._thinking()
        obs_status, obs_result = await self._answer_observation(assistant_message)
        i = 0
        while i < self._max_iter:
            if obs_status == StatusCode.ANSWER:  # return, input or thinking
                if not self._standalone:
                    self._memory.clear()
                    return ChatCompletionAssistantMessageParam(
                        name=self._name, content=obs_result, role="assistant"
                    )
                next_round = self._console.answer(self._memory)
                if next_round:
                    i = 0
                else:
                    return obs_result
            elif obs_status == StatusCode.OBSERVATION:  # thinking
                print()
            elif obs_status == StatusCode.ACTION_FORBIDDEN:  # return None
                return
            else:  # StatusCode.ERROR, StatusCode.NONE, StatusCode.Thought       # return None
                self._console.error(obs_result)
                return
            assistant_message = await self._thinking()
            obs_status, obs_result = await self._answer_observation(assistant_message)
            i += 1
        if i == self._max_iter:
            self._console.overload(self._max_iter)

    # answer or observation
    async def _answer_observation(
        self, chat_message: ChatCompletionMessage
    ) -> Tuple[StatusCode, str]:
        if chat_message.tool_calls:
            for tool_call in chat_message.tool_calls:
                func_name = tool_call.function.name
                func_args = tool_call.function.arguments
                if isinstance(func_args, str):
                    func_args = json.loads(tool_call.function.arguments)

                # validate the tool
                if not func_name in self._functions:
                    return StatusCode.ERROR, f"The '{func_name}' isn't registered!"

                if not self._console.before_action(
                    self._action_permission,
                    func_name,
                    func_args,
                    functions=self._functions,
                ):
                    return (
                        StatusCode.ACTION_FORBIDDEN,
                        "Action cancelled by the user.",
                    )

                status, observation = await self._observation(func_name, func_args)
                if status == StatusCode.OBSERVATION:
                    # append the tool response: observation
                    tool_observation = ChatCompletionToolMessageParam(
                        tool_call_id=tool_call.id,
                        # tool_name=tool_call.function.name, # tool name is not supported by groq client now
                        content=f"{observation}",
                        role="tool",
                    )
                    self._memory.add(
                        self._console.after_action(tool_observation, self._max_obs)
                    )
                else:
                    return status, observation
            return StatusCode.OBSERVATION, "all tool calls were successful!"
        elif chat_message.content:
            # if chat_message.content.startswith(FINAL_ANSWER):
            return (
                StatusCode.ANSWER,
                chat_message.content.replace(FINAL_ANSWER, "").strip(),
            )
        else:
            return (
                StatusCode.NONE,
                f"Invalid response message: {chat_message}",
            )

    async def _observation(self, func_name, func_args) -> Tuple[StatusCode, str]:
        # invoke function
        observation = self._functions[func_name](**func_args)

        # The agent autonomously handles handoffs. https://cookbook.openai.com/examples/orchestrating_agents#executing-routines
        if isinstance(observation, IAgent):
            agent: Agent = observation
            task: str = func_args["message"]

            # self._console.delivery(self.name, agent.name, task)
            ret: ChatCompletionAssistantMessageParam = await agent.run(
                ChatCompletionUserMessageParam(
                    role="user", content=task, name=self.name
                )
                # ChatCompletionUserMessageParam(role="user", content=task)
            )
            if not ret:
                return (
                    StatusCode.ERROR,
                    f"Agent({agent.name}) failed to response: {task}",
                )
            observation = ret.get("content")
            self._console.delivery(agent.name, self.name, observation)
        else:  # default
            self._console.observation(observation)

        return StatusCode.OBSERVATION, observation

    async def async_wrapper_client(self, messages, tools, response_mode):
        return await asyncio.to_thread(self._client, messages, tools, response_mode)

    # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_message_param.py
    # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_tool_param.py
    # https://platform.openai.com/docs/guides/function-calling
    def _add_user_message(self, message: Union[ChatCompletionUserMessageParam, str]):
        if isinstance(message, str):
            message = ChatCompletionUserMessageParam(content=message, role="user")

        self._console.delivery(
            message.get("name", "user"), self.name, message.get("content")
        )
        self._memory.add(message)
