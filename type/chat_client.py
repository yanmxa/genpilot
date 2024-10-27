from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from typing import Protocol, runtime_checkable, Iterable, Union
from .chat_message import ChatMessage
from typing_extensions import TypeAlias


@runtime_checkable
class ChatBinaryClient(Protocol):
    def request(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        tools: Iterable[ChatCompletionToolParam],
    ) -> ChatCompletionMessage:
        """connect the LLM with external tool: https://platform.openai.com/docs/guides/function-calling"""
        ...


@runtime_checkable
class ChatStructuredClient(Protocol):
    def request_format(
        self,
        messages: Iterable[ChatCompletionMessageParam],
    ) -> ChatMessage:
        """Structured outputs: https://platform.openai.com/docs/guides/structured-outputs/introduction"""
        ...


ChatClient: TypeAlias = Union[
    ChatBinaryClient,
    ChatStructuredClient,
]
