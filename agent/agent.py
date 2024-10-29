from abc import ABC, abstractmethod
import datetime
from typing import List

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
)


class Agent(ABC):

    _system: ChatCompletionSystemMessageParam = "You are a magic agent!"

    def _build_system(self, file, mapping) -> str:
        with open(file, "r") as f:
            agent_system = f.read()
        replacements = {
            "{{time}}": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        replacements.update(mapping)
        for placeholder, value in replacements.items():
            agent_system = agent_system.replace(placeholder, value)
        return agent_system

    def _add_system_messages(self, messages: List[ChatCompletionMessageParam]):
        new_messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=self._system,
            )
        ]
        for message in messages:
            new_messages.append(message)
        return new_messages
