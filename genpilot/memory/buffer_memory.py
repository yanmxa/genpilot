from typing import List, Any
from openai.types.chat import (
    ChatCompletionMessageParam,
)

from ..abc.memory import IMemory


class BufferMemory(IMemory):
    def __init__(self, size=10):
        self._messages: List[ChatCompletionMessageParam] = []
        self._size = size
        self._system_message = None

    def add(
        self, message: ChatCompletionMessageParam | List[ChatCompletionMessageParam]
    ):
        if isinstance(message, list):
            self._messages.extend(message)
        else:
            self._messages.append(message)
            if message["role"] == "system":
                self._system_message = message

        # clean up the over size messages
        while len(self._messages) > self._size:
            del self._messages[1]
            if self._messages[1]["role"] == "tool":  # if it is tool call response
                del self._messages[1]

    def pop(self, index=-1) -> ChatCompletionMessageParam:
        return self._messages.pop(index)

    def last(self, default_index=1):
        return self._messages[-default_index]

    def get(self, start=-1, end=-1) -> List[ChatCompletionMessageParam]:
        if start == -1 or start < 0:
            start = 0
        if end == -1 or end > len(self._messages):
            end = len(self._messages)
        return self._messages[start:end]

    def clear(self) -> None:
        self._messages = [self._system_message]
