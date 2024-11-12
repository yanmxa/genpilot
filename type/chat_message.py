from pydantic import BaseModel, Field
import typing
from typing import Optional, List, Any, Dict, Union


class ChatAction(BaseModel):
    name: str = Field(
        ...,
        description="The name of the tool used for this action. Leave this field empty if no tool is available or if providing a direct answer.",
    )
    edit: int = Field(
        0,
        description="Indicates whether the action will modify the system or environment: set to 1 if it will, otherwise set to 0.",
    )
    args: Optional[Dict[str, Any]] = Field(
        {}, description="Arguments to be passed to the tool."
    )


# https://platform.openai.com/docs/guides/structured-outputs/how-to-use
class ChatMessage(BaseModel):
    thought: List[str] = Field(
        ...,  # required
        description="Your thought process regarding the current task or issue.",
    )

    answer: Optional[str] = Field(
        None,
        description="Provide the final answer to the question or task here. If a tool is being used, leave this field empty.",
    )

    action: Optional[ChatAction] = Field(
        None,
        description="Specifies the tool to be used. Leave this field empty if no tool is available or if providing a direct answer.",
    )
