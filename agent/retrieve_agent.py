import os

from typing import Union, List, Protocol
from abc import ABC, abstractmethod

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionAssistantMessageParam,
)

from .agent import IAgent


current_dir = os.path.dirname(os.path.realpath(__file__))
FINAL_ANSWER = "ANSWER:"


class RetrieveAgent(IAgent):

    def __init__(
        self,
        name,
        chat_engine,
    ):
        self._name = name
        self._chat_engine = chat_engine

    @property
    def name(self):
        return self._name

    async def run(
        self, message: Union[ChatCompletionMessageParam, str]
    ) -> ChatCompletionAssistantMessageParam | None:
        if not isinstance(message, str):
            self._standalone = False
            message.get("name", "user"), self.name,
        response = self._chat_engine.chat(message.get("content"))
        return ChatCompletionAssistantMessageParam(
            role="assistant",
            content=f"{response}",
            name=self._name,
        )
