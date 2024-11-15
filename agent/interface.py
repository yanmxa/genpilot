from typing import Union, List
from abc import ABC, abstractmethod

from openai.types.chat import (
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
from memory import ChatMemory


class IAgent(ABC):
    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    async def run(
        self,
        message: Union[ChatCompletionMessageParam, str],
    ) -> ChatCompletionAssistantMessageParam | None:
        pass

    @abstractmethod
    def messages(self) -> List[ChatCompletionMessageParam]:
        pass

    def register_actions(self, tools):
        """
        Register external tools by mapping tool names to their corresponding functions.

        Args:
            tools (List[Callable]): List of tool functions to register.

        Returns:
            dict: Mapping of tool names to tool functions.
        """
        # register the external func(modules) to the agent
        return {tool.__name__: tool for tool in tools}

    def completion_chat_tools(self, tools) -> List[ChatCompletionToolParam]:
        """
        Convert a list of tools into a list of ChatCompletionToolParam objects.

        Args:
            tools (List[Callable]): List of tool functions to process.

        Returns:
            List[ChatCompletionToolParam]: List of structured chat tool parameters.
        """

        # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py#L251
        return [chat_tool(tool) for tool in tools]


class IChat(ABC):

    def system(self, str) -> None:
        pass

    def thinking(self, messages):
        pass

    def delivery(self, from_agent, to_agent, message):
        pass

    async def async_thinking(self, messages, finished_event):
        pass

    def price(self, value):
        pass

    def observation(self, message):
        pass

    def after_action(self, obs: ChatCompletionMessageParam, max_size):
        pass

    def before_thinking(self, memory: ChatMemory) -> bool:
        return self._ask_input(memory, skip_inputs=["", "yes", "approve"])

    def answer(self, memory: ChatMemory) -> bool:
        pass

    def thought(self, result):
        pass

    def error(self, message):
        pass

    def overload(self, max_iter):
        pass

    def before_action(
        self, permission, func_name, func_args, func_edit=0, functions={}
    ) -> bool:
        pass
