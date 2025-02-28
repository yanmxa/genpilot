from abc import ABC, abstractmethod
from enum import Enum
import typing
from typing_extensions import Literal, Required, TypedDict, Optional
from typing import Union, List, Dict
from dataclasses import dataclass

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCall,
)

from .memory import IMemory


class ActionPermission(Enum):
    AUTO = "auto"
    ALWAYS = "always"
    NONE = "none"


class ActionType(Enum):
    AGENT = "agent"
    SERVER = "server"
    FUNCTION = "function"
    NONE = "none"


class ModelConfig(TypedDict, total=False):
    name: Required[str]
    # model_options: https://platform.openai.com/docs/api-reference/chat/create
    config: dict[str, any] = {}


@dataclass
class Attribute:
    name: str
    description: str
    model_name: str
    model_config = {}
    memory: IMemory = None
    model_config: dict = None  # Default value to empty dict
    permission: ActionPermission = ActionPermission.ALWAYS

    def __post_init__(self):
        if self.model_config is None:
            self.model_config = {}


class IAgent(ABC):
    @property
    @abstractmethod
    def attribute(self) -> Attribute:
        pass

    @abstractmethod
    async def __call__(
        self,
        message: Union[ChatCompletionMessageParam, str],
    ) -> ChatCompletionAssistantMessageParam | None:
        """
        define the agent process on here: reasoning/acting
        """
        pass

    @abstractmethod
    async def tool_call(self, func_name, func_args) -> str:
        pass
