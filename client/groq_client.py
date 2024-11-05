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
from client.config import ClientConfig

load_dotenv()


NOT_GIVEN = NotGiven()


class GroqClient:
    def __init__(self, config: ClientConfig):

        self.model_id = config.model
        self.model_temperature = config.temperature
        self.client = Groq(
            api_key=config.api_key,
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
