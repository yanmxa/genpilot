from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Any
from typing import Union, List, Dict

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCall,
)

from genpilot.utils.function_to_schema import func_to_param
from .memory import IMemory


class ActionPermission(Enum):
    AUTO = "auto"
    ALWAYS = "always"
    NONE = "none"


class IAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        pass

    @property
    @abstractmethod
    def memory(self) -> IMemory:
        pass

    @property
    @abstractmethod
    def chat(self):
        pass

    @property
    def permission(self) -> ActionPermission:
        return ActionPermission.ALWAYS

    @abstractmethod
    def run(
        self,
        message: Union[ChatCompletionMessageParam, str],
    ) -> ChatCompletionAssistantMessageParam | None:
        pass

    @abstractmethod
    def functions(self) -> Dict[str, Callable]:
        pass

    def register_tools(self, tools):
        """
        Registers external tools by mapping their names to corresponding functions
        and generating structured chat tool parameters for each tool.

        Args:
            tools (List[Callable]): List of tool functions to register.

        Returns:
            dict: A mapping of tool names to their functions.
            dict: A mapping of tool names to their structured chat tool parameters.
        """
        # Register external functions (modules) to the agent
        # Reference: https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py#L251
        function_map = {tool.__name__: tool for tool in tools}
        tool_map = {tool.__name__: func_to_param(tool) for tool in tools}

        return function_map, tool_map
