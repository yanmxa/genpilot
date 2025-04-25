from abc import ABC, abstractmethod
import enum
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

from .mcp_agent import MCPAgent


class MCPChat(ABC):
    """
    Interface that serves as a proxy for:
    - Interacting with the IAgent to communicate with the user
    - Interfacing with the IAgent to interact with the LLM model
    - Facilitating communication between the IAgent and external tools
    """

    @abstractmethod
    def input(
        self, agent: MCPAgent, message: ChatCompletionMessageParam | str = None
    ) -> bool:
        """
        Forwards the message of user/assistant into chat/memory and format the output message.

        Args:
            agent (IAgent): The agent to process the message.
            message (str): The input message from the user.
              - if none, ask input from an interact input
              - if str, user input
              - if message, assistant input

        Returns:
            bool: whether input the value
        """
        pass

    @abstractmethod
    async def reasoning(self, agent: MCPAgent) -> ChatCompletionAssistantMessageParam:
        """
        Facilitates interaction with the LLM model via the LLM client.

        Args:
            agent (IAgent): The agent to reason with the LLM model.
        """
        pass

    @abstractmethod
    async def acting(self, agent: MCPAgent, func_name, func_args) -> str:
        """
        Enables interaction with external tools.

        Args:
            agent (IAgent): The agent to interact with external tools.
        """
        pass
