from abc import ABC, abstractmethod
from typing import List

from openai.types.chat import (
    ChatCompletionMessageParam,
)


class ChatMemory(ABC):
    """A interface of the model context for both short and long memory.
    The add, get and clear is necessary, while id can be used when you want to persist the memory, summary or experience.
    """

    @property
    def id(self) -> str:
        pass

    @abstractmethod
    def add(self, message: ChatCompletionMessageParam, persistent=False):
        pass

    @abstractmethod
    def get(self, system) -> List[ChatCompletionMessageParam]:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass
