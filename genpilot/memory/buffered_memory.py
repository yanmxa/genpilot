from typing import List, Any
from openai.types.chat import (
    ChatCompletionMessageParam,
)

from ..abc.memory import IMemory


class BufferedMemory(IMemory):
    def __init__(self, size=10):
        self._messages: List[ChatCompletionMessageParam] = []
        self._size = size

    def add(
        self, message: ChatCompletionMessageParam | List[ChatCompletionMessageParam]
    ):
        if isinstance(message, list):
            self._messages.extend(message)
        else:
            self._messages.append(message)

        # clean up the over size messages
        if len(self._messages) > self._size:
            self._messages = self._messages[-self._size :]
            if self._messages[0]["role"] == "tool":
                self._messages = self._messages[1:]

    def pop(self, index=-1) -> ChatCompletionMessageParam:
        return self._messages.pop(index)

    def last(self):
        return self._messages[-1]

    def get(self, start=-1, end=-1) -> List[ChatCompletionMessageParam]:
        if start == -1 or start < 0:
            start = 0
        if end == -1 or end > len(self._messages):
            end = len(self._messages)
        return self._messages[start:end]

    def clear(self) -> None:
        self._messages = []
