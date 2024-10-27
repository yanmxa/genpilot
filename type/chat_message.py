from pydantic import BaseModel, Field
import typing
from typing import Optional, List, Any, Dict


class ChatAction(BaseModel):
    name: str = Field(..., description="The tool name used for the action")
    edit: int = Field(
        0,
        description="Whether the tool or action will update your system or environment, if it is, then return 1, else return 0",
    )
    args: Optional[Dict[str, Any]] = Field(
        {}, description="The arguments passed to the tool."
    )


# https://platform.openai.com/docs/guides/structured-outputs/how-to-use
class ChatMessage(BaseModel):
    thought: List[str] = Field(
        ...,  # required
        description="Represents your thought process regarding the current task. This field is used to plan the solution and outline the next steps. Print paragraphs with appropriate delimiters to make your ideas clearer",
    )

    answer: Optional[str] = Field(
        None,
        description="At the end of the task, give the final answer for initial question or task. Then the thought should be the summarization of the whole process!",
    )

    action: Optional[ChatAction] = Field(
        None,
        description="Describes the tool needed to gather knowledge or perform actions.",
    )
