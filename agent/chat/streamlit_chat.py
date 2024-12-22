import rich.rule
import streamlit as st
import typing
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionMessage,
)
from typing import Callable, Any
from memory import ChatMemory
from ..interface.chat import IChat
from .common import assistant_message_to_param
import streamlit as st


def get_tool_message(tool_call: ChatCompletionMessageToolCall):
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


class StreamlitChat(IChat):
    @classmethod
    def context(cls, config):
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

    @classmethod
    def is_init_session(cls) -> bool:
        return "agent" in st.session_state

    @classmethod
    def init_session(cls, agent):
        st.session_state.agent = agent
        st.session_state.messages = []

    @classmethod
    def input_message(cls):
        agent = st.session_state.agent
        if user_input := st.chat_input("Ask a question"):
            if user_input == "/debug":
                st.write(agent._memory.get(None))
            else:
                agent.run(user_input)

    def __init__(self, name="user", avatar="🤖"):
        self._before_thinking = False
        self.name = name
        self.avatar = avatar
        self.role = "assistant"

    def system(self, message: str):
        pass

    def avatar(self):
        return self.avatar

    def input(self, message, from_agent_name="user", from_agent_avatar="👨‍💻"):
        with st.chat_message(from_agent_name, avatar=from_agent_avatar):
            st.markdown(message.get("content"))

    def assistant_thinking(
        self, task_func: Callable[..., Any], *args: Any
    ) -> ChatCompletionMessageParam:
        # Show bot response with a spinner
        with st.chat_message(self.name, avatar=self.avatar):
            # Wrapping spinner and message content in a flex container
            with st.empty():  # This allows to add dynamic elements like the spinner
                with st.spinner("Thinking..."):  # Spinner icon
                    message, price = task_func(*args)

                    assistant_param: ChatCompletionAssistantMessageParam = (
                        assistant_message_to_param(message, self.name)
                    )

                    # message is ChatCompletionMessage
                    # st.session_state.messages.append(message)

                    # assert message is a tool call or content
                    print_message = assistant_param.get("content")
                    if assistant_param.get("tool_calls"):
                        # the the tool call print message
                        print_message = get_tool_message(
                            assistant_param.get("tool_calls")[0]
                        )

                    if price is not None and price != "":
                        print_message = print_message + f"\n [$] {price}"

                st.markdown(print_message, unsafe_allow_html=True)
        return assistant_param

    def before_thinking(self, memory: ChatMemory, tools=[]) -> bool:
        return True

    def observation(self, obs) -> str:
        """
        Must return the change obs
        """
        print(obs)
        print_message = f"""<div style="
          color: gray; 
          font-size: 0.9em; 
          font-style: italic;">
          {obs.get("content")}
          </div>
          """
        with st.chat_message(self.name, avatar="🔧"):
            st.markdown(print_message, unsafe_allow_html=True)
        return obs

    def next_message(self, memory: ChatMemory, tools=[]) -> str:

        import rich

        for message in memory.get(None):
            rich.print(f"{message.get('role')} -> {type(message)}")
            rich.print(message)
        return ""

    def error(self, message):
        with st.chat_message(self.name, avatar=self.avatar):
            st.markdown(message)

    def before_action(
        self, permission, func_name, func_args, func_edit=0, functions={}
    ) -> bool:
        return True
