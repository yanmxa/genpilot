import boto3
from botocore.exceptions import ClientError
import os
from rich.console import Console
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)
from openai.types import FunctionDefinition, FunctionParameters
from openai.types.chat.chat_completion_message_tool_call import Function
from typing import Iterable
import rich

from dotenv import load_dotenv
import rich.json
from client.config import ClientConfig

load_dotenv()


console = Console()


# We will not address compatibility between this SDK and the OpenAI SDK. For other client SDKs, we will use structured content to directly wrap the tools' information.
class BedRockClient:
    def __init__(self, config: ClientConfig):
        # reference: https://community.aws/content/2hHgVE7Lz6Jj1vFv39zSzzlCilG/getting-started-with-the-amazon-bedrock-converse-api?lang=en
        self.model_id = config.model
        self.inference_config = config.ext["inference_config"]
        self.price_per_1000_input = config.price_1k_token_in
        self.price_per_1000_output = config.price_1k_token_out
        self.total_price = 0

        session = boto3.Session()
        self.client = session.client(
            "bedrock-runtime",
            region_name=os.getenv("AWS_REGION_NAME"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

    def __call__(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        tools: Iterable[ChatCompletionToolParam],
    ):

        message_list = []
        for msg in messages:
            if isinstance(msg, ChatCompletionMessage):
                content = [{"text": msg.content}]
                if msg.role == "system":
                    system_message = content
                else:
                    message_list.append({"role": msg.role, "content": content})
            else:
                content = [{"text": msg["content"]}]
                if msg["role"] == "system":
                    system_message = content
                else:
                    message_list.append({"role": msg["role"], "content": content})

        while len(message_list) > 0 and message_list[0]["role"] != "user":
            message_list.pop(0)

        # import rich
        # rich.get_console().print(message_list)
        response = self.client.converse(
            modelId=self.model_id,
            messages=message_list,
            system=system_message,
            inferenceConfig=self.inference_config,
            # toolConfig={"tools": tool_list},
        )
        # price
        usage = response["usage"]
        cost = calculate_llm_price(
            usage["inputTokens"],
            usage["outputTokens"],
            self.price_per_1000_input,
            self.price_per_1000_output,
        )
        self.total_price += cost
        return (
            ChatCompletionMessage(
                role="assistant",
                content=response["output"]["message"]["content"][0]["text"],
            ),
            self.total_price,
        )


def calculate_llm_price(
    input_tokens, output_tokens, price_per_1000_input, price_per_1000_output
):
    # Convert token counts to thousands and multiply by respective rates
    input_cost = (input_tokens / 1000) * price_per_1000_input
    output_cost = (output_tokens / 1000) * price_per_1000_output
    total_cost = input_cost + output_cost
    return total_cost
