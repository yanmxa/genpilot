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
    ChatCompletionMessage,
)
from memory import ChatMemory
from typing import Callable, Any


class IChat(ABC):

    def system(self, str) -> None:
        pass

    @property
    @abstractmethod
    def avatar(self):
        pass

    # def delivery(self, message, from_agent, to_agent, avatar=None):
    #     pass

    def input(self, message, from_agent_name=None, from_agent_avatar=None):
        pass

    def before_action(
        self, permission, func_name, func_args, func_edit=0, functions={}
    ) -> bool:
        pass

    def observation(self, message) -> str:
        pass

    def before_thinking(self, memory: ChatMemory) -> bool:
        pass

    def assistant_thinking(
        self, task_func: Callable[..., Any], *args: Any
    ) -> ChatCompletionMessageParam:
        pass

    # def answer(self, memory: ChatMemory) -> bool:
    #     pass

    def next_message(self, memory: ChatMemory, tools=[]) -> str:
        pass

    def error(self, message):
        pass
