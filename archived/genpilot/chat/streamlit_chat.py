import rich.console
import rich
import rich.rule
from typing import Callable, Any, List, Tuple, Union

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
    @classmethod
    def set_page_config(cls, config):
        st.set_page_config(**config)
        st.markdown(
            """
          <style>
              .reportview-container {
                  margin-top: -2em;
              }
              #MainMenu {visibility: hidden;}
              .stAppDeployButton {display:none;}
              footer {visibility: hidden;}
              #stDecoration {display:none;}
          </style>
        """,
            unsafe_allow_html=True,
        )

    # init session state
    @classmethod
    def add_chat_session(cls, agent_factory):
        if "agent" not in st.session_state:
            st.session_state.agent = agent_factory()

        # render messages in here
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for msg in st.session_state.messages:
            with st.chat_message(msg["name"], avatar=msg["avatar"]):
                st.markdown(
                    msg["content"],
                    unsafe_allow_html=True,
                )

        agent: IAgent = st.session_state.agent
        rprint(f"session: agent running starts")
        result = agent.run()
        rprint(f"session: agent running finished!")

    # Optional OpenAI params: see https://platform.openai.com/docs/api-reference/chat/create
    def __init__(
        self,
        model_options,
        avatars={},
    ):
        self.console = rich.get_console()
        self.model_options = model_options
        self.avatars = {
            "user": "👦",
            "assistant": "🤖",
            "system": "💻",
            "tool": "🛠",
        } | avatars

    def get_avatar(self, name, role="assistant"):
        return self.avatars.get(name, self.avatars.get(role))

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
                rprint(f"input message {message}")
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

        if message is None:
            return None

        msg = st.session_state.messages[-1]
        if msg["name"] == "user":
            with st.chat_message(msg["name"], avatar=msg["avatar"]):
                st.markdown(
                    msg["content"],
                    unsafe_allow_html=True,
                )
        return message

    def reasoning(self, agent: IAgent) -> ChatCompletionAssistantMessageParam:
        # human in loop
        tools = list(agent.tools.values())
        response = None
        avatar = self.avatars.get(agent.name, self.avatars.get("assistant"))

        # self.console.print(agent.memory._messages)

        try:

            with st.chat_message(agent.name, avatar=avatar):
                # Wrapping spinner and message content in a flex container
                with st.empty():  # This allows to add dynamic elements like the spinner
                    with st.spinner("Thinking..."):  # Spinner icon
                        response = completion(
                            model=agent.model,
                            messages=agent.memory.get(),
                            tools=tools,
                            **self.model_options,
                        )
                    completion_message, print_message = self.reasoning_print(
                        response, agent
                    )
                    # rprint(f"{agent.name} print message {print_message}")
                    st.markdown(print_message, unsafe_allow_html=True)
                    st.session_state.messages.append(
                        {
                            "name": agent.name,
                            "avatar": avatar,
                            "content": print_message,
                        }
                    )

        except Exception as e:
            self.console.print(agent.memory.get())
            print(f"Exception Message: {str(e)}")
            import traceback

            traceback.print_exc()

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
    ) -> Tuple[ChatCompletionMessage, str]:

        # not print agent tools calls in this function, only print the content
        completion_message = ChatCompletionMessage(role="assistant")
        print_message = ""
        if isinstance(response, CustomStreamWrapper):
            raise ValueError("stream output isn't supported")
        else:
            completion_message = response.choices[0].message
            if completion_message.content:
                # Scenario 2: print complete content and tool call info
                print_message = completion_message.content
            elif completion_message.tool_calls:
                for tool_call in completion_message.tool_calls:
                    print_message += self.too_output(tool_call)
        return completion_message, print_message

    def acting(self, agent: IAgent, func_name, func_args) -> str:
        func = agent.functions[func_name]
        observation = ""
        with st.chat_message(agent.name, avatar="👀"):
            # Wrapping spinner and message content in a flex container
            with st.empty():  # This allows to add dynamic elements like the spinner
                with st.spinner("Invoking..."):  # Spinner icon
                    observation = func(**func_args)
                    print_message = f"""<div style="
                          color: gray; 
                          font-size: 0.9em; 
                          font-style: italic;">
                          {observation}
                          </div>
                      """

                st.markdown(print_message, unsafe_allow_html=True)
                st.session_state.messages.append(
                    {
                        "name": agent.name,
                        "avatar": "👀",
                        "content": print_message,
                    }
                )

        return observation

    def too_output(self, tool_call: ChatCompletionMessageToolCall):
        if tool_call.function.name == "code_executor":
            func_args = tool_call.function.arguments
            # print(tool_call.function)
            if isinstance(func_args, str):
                import json

                func_args = json.loads(tool_call.function.arguments)
            lang = func_args["language"]
            code = func_args["code"]
            print(f"{lang} -> {code}")
            # st.code(code, language=lang)
            return f"```{lang}\n{code}\n```"
        else:
            return f"""
                <div style="
                    padding: 10px; 
                    border-radius: 5px; 
                    background-color: #FFF9C4; 
                    margin-bottom: 10px;">
                    <strong>🔧 Tool:</strong> {tool_call.function.name}<br>
                    <strong>📄 Args:</strong> {tool_call.function.arguments}
                </div>
                """
