import os
from groq import Groq
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
import instructor
from openai.types import FunctionDefinition, FunctionParameters
from openai import NotGiven
from typing import Iterable
from pydantic import BaseModel
import rich

from dotenv import load_dotenv
from client.config import ClientConfig

load_dotenv()


NOT_GIVEN = NotGiven()


class GroqClient:
    def __init__(self, config: ClientConfig):

        self.model_id = config.model
        self.model_temperature = config.temperature
        self._grop_client = Groq(
            api_key=config.api_key,
        )
        if config.mode == instructor.Mode.JSON:
            self._client = instructor.from_groq(
                self._grop_client, mode=instructor.Mode.JSON
            )

    def __call__(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        tools: Iterable[ChatCompletionToolParam],
        response_model: BaseModel = None,
    ) -> ChatCompletionMessage:
        # https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py
        if response_model:
            chat_completion: BaseModel = self._client.chat.completions.create(
                stream=False,
                model=self.model_id,
                temperature=self.model_temperature,
                messages=messages,
                tools=tools,
                response_model=response_model,
                # response_format=ResponseFormat, #TODO: the llama api current doesn't support structured output
            )
            return (
                ChatCompletionMessage(
                    content=response_model.model_dump_json(chat_completion),
                    role="assistant",
                ),
                "",
            )

        chat_completion = self._grop_client.chat.completions.create(
            stream=False,
            model=self.model_id,
            temperature=self.model_temperature,
            messages=messages,
            tools=tools,
            # response_format=ResponseFormat, #TODO: the llama api current doesn't support structured output
        )
        return chat_completion.choices[0].message, ""
