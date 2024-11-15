from typing import List, Any
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
)

from .chat_memory import ChatMemory


# ChatBufferMemory is a short-term memory implementation designed to retrieve the most recent message along with the current session context.
class ChatBufferMemory(ChatMemory):
    def __init__(self, memory_id="", size=3):
        self._memory_id = memory_id
        self._messages: List[ChatCompletionMessageParam] = []
        self._size = size

    @property
    def id(self) -> str:
        return self._memory_id

    def add(self, message: ChatCompletionMessageParam, persistent=False):
        self._messages.append(message)
        if len(self._messages) > self._size:
            self._messages = self._messages[-self._size :]
        if self._messages[0]["role"] == "tool":
            self._messages = self._messages[1:]

    def pop(self, index=-1) -> ChatCompletionMessageParam:
        return self._messages.pop(index)

    def get(self, system) -> List[ChatCompletionMessageParam]:
        new_messages = []
        if system:
            new_messages.append(
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=system,
                )
            )
        for message in self._messages:
            new_messages.append(message)
        return new_messages

    def clear(self) -> None:
        self._messages = []
