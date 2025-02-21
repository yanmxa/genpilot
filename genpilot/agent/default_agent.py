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
import aisuite as ai

import genpilot as gp
from ..abc.agent import IAgent
from ..abc.memory import IMemory
from ..abc.chat import IChat


class Agent(IAgent):

    def __init__(
        self,
        name,
        system,
        tools=[],
        model="",
        chat: IChat = None,
        memory: IMemory = None,
        # TODO: consider introduce terminate condition with autogen 4.0
        max_iter=6,
    ):
        self._name = name
        self._functions, self.tools = self.register_tools(tools)
        self._model = model

        # TODO: give a default chat console
        self._chat = chat
        self._memory = (
            memory if memory is not None else gp.memory.BufferedMemory(size=10)
        )
        self._memory.add(
            ChatCompletionSystemMessageParam(content=system, role="system", name=name)
        )

        self._max_iter = max_iter

    @property
    def name(self):
        return self._name

    @property
    def model(self):
        return self._model

    @property
    def chat(self):
        return self._chat

    @property
    def functions(self):
        return self._functions

    @property
    def memory(self):
        return self._memory

    # def chatbot(self):
    #     print()
    #     message = self.chat_console.next_message(self._memory, tools=self._tools)
    #     return self.run(message)

    def run(
        self,
        message: Union[ChatCompletionMessageParam, str, None],
    ) -> ChatCompletionAssistantMessageParam | str | None:

        # 1. verify the message, whether to stop the conversation
        if isinstance(message, str):
            message = ChatCompletionUserMessageParam(
                content=message, role="user", name="user"
            )
        message = self.chat.input(message, self)
        if message is None:
            self.memory.clear()
            return None

        i = 0
        while i == 0 or i < self._max_iter:
            # 2. reasoning
            assistant_message: ChatCompletionAssistantMessageParam = (
                self.chat.reasoning(agent=self)
            )
            assistant_message["name"] = self.name
            self.memory.add(assistant_message)

            # 3. actioning
            tool_messages: List[ChatCompletionToolMessageParam] = self.chat.acting(
                agent=self
            )

            # 4. if tool_messages exists, then it is a tool call observation, else it is the assistant response
            if tool_messages is None or len(tool_messages) == 0:
                self.memory.clear()
                return assistant_message

            self.memory.add(tool_messages)

            i += 1
        if i >= self._max_iter:
            self.memory.clear()
            return f"Reached maximum iterations: {self._max_iter}!"
