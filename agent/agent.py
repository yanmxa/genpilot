import os
import json
from typing import Union, Tuple, List, Protocol
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
from type import StatusCode, ActionPermission

from memory import ChatMemory, ChatBufferMemory
from agent.interface.chat import IChat
from agent.interface.agent import IAgent
from agent.chat.terminal_chat import TerminalChat

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
        chat_console: IChat | None = None,
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
        self._user_input = True
        self._action_permission = action_permission
        self._memory = (
            memory if memory is not None else ChatBufferMemory(memory_id=name, size=10)
        )
        self._console = chat_console if chat_console is not None else TerminalChat(name)
        # self.avatar = self._console.avatar
        self._max_iter = max_iter
        self._max_obs = max_obs
        self._is_terminal = is_terminal

        self._console.system(self._system)

        self._response_model = response_model

    @property
    def name(self):
        return self._name

    @property
    def avatar(self):
        return self._console.avatar

    def messages(self) -> List[ChatCompletionMessageParam]:
        return self._memory.get(None)

    # Give the assistant response based on the memory messages
    def _thinking(self) -> ChatCompletionAssistantMessageParam:
        new_messages = self._memory.get(self._system)
        assistant_param = self._console.assistant_thinking(
            self._client, new_messages, self._tools, self._response_model
        )
        self._memory.add(assistant_param)
        return assistant_param

    def run(
        self,
        message: Union[ChatCompletionMessageParam, str],
    ) -> ChatCompletionAssistantMessageParam | None:

        # 1. Inputting message into the memory
        is_user_input = self._input(message)
        # 2. Reasoning: the assistant response message into the memory
        assistant_message = self._thinking()
        # 3. Actioning: the assistant response message
        status, result = self._acting()
        i = 0
        while i < self._max_iter:
            if status == StatusCode.ANSWER:  # return, input or thinking
                if not self._user_input:
                    self._memory.clear()
                    return ChatCompletionAssistantMessageParam(
                        name=self._name, content=result, role="assistant"
                    )
                message = self._console.next_message(self._memory, tools=self._tools)
                if message:
                    i = 0
                    is_user_input = self._input(message)
                else:
                    return result
            elif status == StatusCode.OBSERVATION:  # thinking
                print()  # tool call observation, then thinking
            elif status == StatusCode.ACTION_FORBIDDEN:  # return None
                return ChatCompletionUserMessageParam(
                    role="user", content=result, name=self.name
                )
            else:  # StatusCode.ERROR, StatusCode.NONE, StatusCode.Thought       # return None
                self._console.error(result)
                return ChatCompletionUserMessageParam(
                    role="user", content=result, name=self.name
                )
            assistant_message = self._thinking()
            status, result = self._acting()
            i += 1
        if i == self._max_iter:
            self._console.error(f"Reached maximum iterations: {self._max_iter}!\n")

    # answer or observation
    def _acting(self) -> Tuple[StatusCode, str]:
        chat_assistant_param = self._memory.get(None)[-1]
        if chat_assistant_param.get("tool_calls"):
            for tool_call in chat_assistant_param.get("tool_calls"):
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
                        f"Action{func_name} are not allowed by the user.",
                    )

                err_message = self._observation(tool_call.id, func_name, func_args)
                if err_message:
                    return StatusCode.ERROR, err_message
            return StatusCode.OBSERVATION, "all tool calls were successful!"
        elif chat_assistant_param.get("content"):
            # if chat_message.content.startswith(FINAL_ANSWER):
            return (
                StatusCode.ANSWER,
                chat_assistant_param.get("content").replace(FINAL_ANSWER, "").strip(),
            )
        else:
            return (
                StatusCode.NONE,
                f"Invalid response message: {chat_assistant_param}",
            )

    # save the observation into the memory, return error message
    def _observation(self, tool_call_id, func_name, func_args) -> None | str:
        # invoke function
        observation = self._functions[func_name](**func_args)

        # The agent autonomously handles handoffs. https://cookbook.openai.com/examples/orchestrating_agents#executing-routines
        if isinstance(observation, IAgent):
            agent: Agent = observation
            task: str = func_args["message"]

            # self._console.delivery(self.name, agent.name, task)
            agent_observation: ChatCompletionAssistantMessageParam = agent.run(
                ChatCompletionUserMessageParam(
                    role="user", content=task, name=self.name
                )
                # ChatCompletionUserMessageParam(role="user", content=task)
            )
            if not agent_observation:
                return f"Agent({agent.name}) failed to handle the task: {task}"
            is_user_input = self._input(agent_observation, agent.name, agent.avatar)
            # self._console.delivery(observation, agent.name, self.name, agent.avatar)
        else:  # default
            # append the tool response: observation
            tool_observation = ChatCompletionToolMessageParam(
                tool_call_id=tool_call_id,
                # tool_name=tool_call.function.name, # tool name is not supported by groq client now
                content=f"{observation}",
                role="tool",
            )
            self._memory.add(tool_observation)
            observation = self._console.observation(tool_observation)
        return None

    # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_message_param.py
    # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_tool_param.py
    # https://platform.openai.com/docs/guides/function-calling
    def _input(
        self,
        message: Union[ChatCompletionUserMessageParam, str],
        agent_name: str = "user",
        agent_avatar: str = "👨‍💻",
    ) -> bool:
        """_summary_
        Returns:
            bool: whether the message is user input
        """
        is_user_input = False
        if isinstance(message, str):
            self._user_input = True
            message = ChatCompletionUserMessageParam(content=message, role="user")
        self._memory.add(message)
        self._console.input(message, agent_name, agent_avatar)
        return is_user_input
