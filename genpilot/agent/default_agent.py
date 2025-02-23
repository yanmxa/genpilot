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

            if (
                "tool_calls" not in assistant_message
                or assistant_message["tool_calls"] is None
            ):
                self.memory.clear()
                return assistant_message

            assistant_message["name"] = self.name  # add agent name to the function call
            self.memory.add(assistant_message)

            # 3. actioning
            for tool_call in assistant_message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = tool_call["function"]["arguments"]
                tool_call_id = tool_call["id"]
                if isinstance(func_args, str):
                    func_args = json.loads(func_args)
                # validate
                if not func_name in self.functions:
                    raise ValueError(f"The '{func_name}' isn't registered!")

                func = self.functions[func_name]
                return_type = func.__annotations__.get("return")
                # agent invoking
                if return_type is not None and issubclass(return_type, IAgent):
                    target_agent: IAgent = func(**func_args)
                    target_message = ChatCompletionAssistantMessageParam(
                        role="assistant", content=func_args["message"], name=self.name
                    )
                    target_response: ChatCompletionAssistantMessageParam = (
                        target_agent.run(target_message)
                    )
                    if target_response is None:
                        raise ValueError(
                            f"The agent{target_agent.name} observation is None!"
                        )
                    if isinstance(target_response, str):
                        raise ValueError(
                            f"{target_agent.name} error: {target_response}"
                        )
                    content = target_response["content"]
                    self.memory.add(
                        ChatCompletionToolMessageParam(
                            tool_call_id=tool_call_id,
                            content=f"{content}",
                            role="tool",
                            name=func_name,
                        )
                    )
                # function invoking
                else:
                    func_result = self.chat.acting(self, func_name, func_args)
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
