import rich.console
import sys
import rich
import rich.rule
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown
from rich.padding import Padding
import threading
from rich.padding import Padding
from typing import Callable, Any, List, Tuple, Union
import time
from datetime import datetime
import json
from enum import Enum

from litellm import completion
from litellm.utils import (
    ModelResponse,
    CustomStreamWrapper,
    ChatCompletionDeltaToolCall,
)
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion_message_tool_call import Function

from ..abc.agent import IAgent
from ..abc.chat import IChat

import streamlit as st


class StreamlitChat(IChat):
    # Optional OpenAI params: see https://platform.openai.com/docs/api-reference/chat/create
    def __init__(self, model_options):
        self.console = rich.get_console()
        self.model_options = model_options
        self.avatars = {
            "user": "👦",
            "assistant": "🤖",
            "system": "💻",
            "tool": "🛠",
        }
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def get_avatar(self, name, role="assistant"):
        # return self.avatars.get(name, self.avatars.get(role))
        return name

    def input(
        self, message: ChatCompletionMessageParam | str | None, agent: IAgent
    ) -> ChatCompletionMessageParam | None:
        if isinstance(message, str):
            message = ChatCompletionUserMessageParam(
                content=message, role="user", name="user"
            )

        if message is None:
            user_input = st.chat_input("Ask a question")
            if user_input == "/debug":
                st.write(agent.memory.get())
            elif user_input == "/clear":
                # clean both ui and agent
                st.session_state.messages = []
                agent.memory.clear()
            elif user_input is not None:
                message = ChatCompletionUserMessageParam(
                    role="user", name="user", content=user_input
                )
                print(f"print message {message}")
        if message is not None:
            # add the both ui and agent memory
            st.session_state.messages.append(
                {
                    "name": message["name"],
                    "avatar": self.get_avatar(message["name"], message["role"]),
                    "content": message.get("content"),
                }
            )
            agent.memory.add(message)

        # print all
        for msg in st.session_state.messages:
            st.chat_message(msg.get("name")).markdown(
                msg.get("content"),
                unsafe_allow_html=True,
            )
        return message

    def reasoning(self, agent: IAgent) -> ChatCompletionAssistantMessageParam:
        # human in loop
        tools = list(agent.tools.values())
        response = None
        avatar = self.avatars.get(agent.name, self.avatars.get("assistant"))

        #
        self.console.print(agent.memory.get())
        try:
            with self.console.status(
                f"{avatar} [cyan]{agent.name} ...[/]", spinner="aesthetic"
            ):
                response = completion(
                    model=agent.model,
                    messages=agent.memory.get(),
                    tools=tools,
                    **self.model_options,
                )
        except Exception as e:
            self.console.print(agent.memory.get())
            print(f"Exception Message: {str(e)}")
            import traceback

            traceback.print_exc()

        completion_message = self.reasoning_print(response, agent)

        message = completion_message.model_dump(mode="json")
        # for 'role:assistant' the following must be satisfied[('messages.2' : property 'refusal' is unsupported
        if message["role"] == "assistant" and "refusal" in message:
            del message["refusal"]
        return message

    def stream_content(self, response: CustomStreamWrapper):
        for chunk in response:
            delta = chunk.choices[0].delta
            # # if delta.tool_calls is not None:
            # #     for delta_tool_call in delta.tool_calls:
            # #         # tool_call is ChatCompletionDeltaToolCall
            # #         completion_message_tool_calls.append(
            # #             ChatCompletionMessageToolCall(
            # #                 id=delta_tool_call.id,
            # #                 function=Function(
            # #                     arguments=delta_tool_call.function.arguments,
            # #                     name=delta_tool_call.function.name,
            # #                 ),
            # #                 type=delta_tool_call.type,
            # #             )
            # #         )

            # if delta.content is not None and delta.content != "":
            # Scenario 1: print delta content
            yield delta

    def reasoning_print(
        self, response: Union[ModelResponse, CustomStreamWrapper], agent: IAgent
    ) -> ChatCompletionMessage:

        # not print agent tools calls in this function, only print the content
        completion_message = ChatCompletionMessage(role="assistant")
        if isinstance(response, CustomStreamWrapper):
            completion_message_tool_calls: List[ChatCompletionMessageToolCall] = []
            completion_message_content = ""
            print_content = False
            with st.chat_message(agent.name, self.get_avatar(agent.name, "assistant")):
                deltas = st.write_stream(self.stream_content(response))
                self.console.print(deltas)
        else:
            completion_message = response.choices[0].message
            if completion_message.content:
                # Scenario 2: print complete content
                with st.chat_message(name=agent.name):
                    st.write(completion_message.content)

        return completion_message

    def acting(self, agent: IAgent, func_name, func_args) -> str:
        func = agent.functions[func_name]
        result = func(**func_args)

        return result
