from abc import ABC, abstractmethod
from typing import Union, List

from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCall,
)

from .agent import IAgent


class IChat(ABC):
    """
    Interface that serves as a proxy for:
    - Interacting with the IAgent to communicate with the user
    - Interfacing with the IAgent to interact with the LLM model
    - Facilitating communication between the IAgent and external tools
    """

    @abstractmethod
    def input(
        self, message: ChatCompletionMessageParam | str | None, agent: IAgent
    ) -> ChatCompletionMessageParam | None:
        """
        Forwards the message of user/assistant into chat/memory and format the output message.

        Args:
            message (str): The input message from the user.
            agent (IAgent): The agent to process the message.

        Returns:
            message: the formatted output message. None indicates the end of the conversation.
        """
        pass

    @abstractmethod
    def reasoning(self, agent: IAgent) -> ChatCompletionAssistantMessageParam:
        """
        Facilitates interaction with the LLM model via the LLM client.

        Args:
            agent (IAgent): The agent to reason with the LLM model.
        """
        pass

    @abstractmethod
    def acting(self, agent: IAgent, func_name, func_args) -> str:
        """
        Enables interaction with external tools.

        Args:
            agent (IAgent): The agent to interact with external tools.
        """
        pass
