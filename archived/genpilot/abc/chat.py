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

from .agent import ActionType, IAgent


class IChat(ABC):
    """
    Interface that serves as a proxy for:
    - Interacting with the IAgent to communicate with the user
    - Interfacing with the IAgent to interact with the LLM model
    - Facilitating communication between the IAgent and external tools
    """

    @abstractmethod
    def input(self, agent: IAgent, message: ChatCompletionMessageParam = None) -> bool:
        """
        Input the the init message into agent

        Args:
            message (str): The input message from the user.
            agent (IAgent): The agent to process the message.

        Returns:
            bool: whether input message
        """
        pass

    @abstractmethod
    async def reasoning(
        self, agent: IAgent, tool_schemas: List
    ) -> ChatCompletionAssistantMessageParam:
        """
        Facilitates interaction with the LLM model via the LLM client.

        Args:
            agent (IAgent): The agent to reason with the LLM model.
        """
        pass

    @abstractmethod
    async def acting(
        self, agent: IAgent, action_type: ActionType, func_name, func_args
    ) -> str:
        """
        Enables interaction with external tools.

        Args:
            agent (IAgent): The agent to interact with external tools.
        """
        pass
