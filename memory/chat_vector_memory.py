from typing import List, Any
from llama_index.core.memory import VectorMemory
from llama_index.core.base.llms.types import ChatMessage
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionUserMessageParam,
)

from test import vector_memory
from .chat_memory import ChatMemory


# The ChatVectorMemory is a default implementation for long-term memory, based on the LlamaIndex vector memory. For more information, visit the documentation: LlamaIndex Vector Memory.
class ChatVectorMemory(ChatMemory):
    def __init__(self, memory_id="", buffer_size=6, vector_memory: VectorMemory = None):
        self._memory_id = memory_id
        self._messages: List[ChatCompletionMessageParam] = []
        self._size = buffer_size
        self._vector_memory = vector_memory

    @property
    def id(self) -> str:
        return self._memory_id

    def add(self, message: ChatCompletionMessageParam):
        self._messages.append(message)
        if len(self._messages) > self._size:
            self._messages = self._messages[-self._size :]
        # add the vector
        if self._target_vector_message(message):
            msg = ChatMessage(role=message.get("role"), content=message.get("content"))
            self._vector_memory.put(msg)

    def get(self, system) -> List[ChatCompletionMessageParam]:
        new_system = system
        # add context to system by the vector memory
        last_message = self._messages[-1]
        if self._target_vector_message(last_message):
            chat_msgs: List[ChatMessage] = self._vector_memory.get(last_message)
            if len(chat_msgs) > 0:
                # refer: https://docs.llamaindex.ai/en/stable/examples/agent/memory/composable_memory/
                memories = [
                    "Below are a set of relevant dialogues retrieved from memory:",
                    "=====Relevant messages from memory=====",
                ]
                for msg in chat_msgs:
                    memories.append(f"  {msg.role}: {msg.content}")
                memories.append("=====End of relevant messages from memory======")
                context = "\n".join(memories)
                new_system = f"SYSTEM: {system} \n {context}"

        new_messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=new_system,
            )
        ]
        for message in self._messages:
            new_messages.append(message)
        return new_messages

    def clear(self) -> None:
        self._messages = []

    def _target_vector_message(self, message: ChatCompletionMessageParam) -> bool:
        if self._vector_memory is None:
            raise ValueError("the vector memory is not set for the ChatVectorMemory")
        if isinstance(message, ChatCompletionAssistantMessageParam) or isinstance(
            message, ChatCompletionUserMessageParam
        ):
            return True

        return False
