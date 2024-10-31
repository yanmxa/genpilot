import os
from groq import Groq
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from openai.types import FunctionDefinition, FunctionParameters
from openai import NotGiven
from typing import Iterable
import rich

from dotenv import load_dotenv

load_dotenv()


NOT_GIVEN = NotGiven()


class GroqClient:
    def __init__(self):
        self.model_id = "llama3-70b-8192"
        self.model_temperature = 0.2
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY"),
        )

    def __call__(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        tools: Iterable[ChatCompletionToolParam],
    ) -> ChatCompletionMessage:
        # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py
        chat_completion = self.client.chat.completions.create(
            stream=False,
            model=self.model_id,
            temperature=self.model_temperature,
            messages=messages,
            tools=tools,
            # response_format=ResponseFormat, #TODO: the llama api current doesn't support structured output
        )
        return chat_completion.choices[0].message, ""
