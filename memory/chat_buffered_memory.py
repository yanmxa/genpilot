from typing import List, Any
from openai.types.chat import (
    ChatCompletionMessageParam,
)
from .chat_memory import ChatMemory


class ChatBufferedMemory(ChatMemory):
    def __init__(self, memory_id="", size=3):
        self._memory_id = memory_id
        self._messages: List[ChatCompletionMessageParam] = []
        self._size = size

    @property
    def id(self) -> str:
        return self._memory_id

    def add(self, message: ChatCompletionMessageParam):
        self._messages.append(message)
        if len(self._messages) > self._size:
            self._messages = self._messages[-self._size :]

    def get(self) -> List[ChatCompletionMessageParam]:
        return self._messages

    def clear(self) -> None:
        self._messages = []
