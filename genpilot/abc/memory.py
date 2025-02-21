from abc import ABC, abstractmethod
from typing import List

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCall,
)


class IMemory(ABC):

    # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion_message_param.py#L17
    @abstractmethod
    def add(
        self, message: ChatCompletionMessageParam | List[ChatCompletionMessageParam]
    ):
        pass

    @abstractmethod
    def last(self) -> ChatCompletionMessageParam:
        pass

    @abstractmethod
    def get(
        self,
        start=-1,
        end=-1,
    ) -> List[ChatCompletionMessageParam]:
        pass

    @abstractmethod
    def pop(self) -> ChatCompletionMessageParam:
        pass

    @abstractmethod
    def clear(self):
        pass
