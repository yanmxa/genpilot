import boto3
from botocore.exceptions import ClientError
import instructor
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
from typing import Iterable, List
import rich
import json

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
        self._boto3_client = session.client(
            "bedrock-runtime",
            region_name=os.getenv("AWS_REGION_NAME"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

    def __call__(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        tools: Iterable[ChatCompletionToolParam],
        response_model=None,
    ):

        # rich.get_console().print(messages)
        message_list = []
        for msg in messages:
            if isinstance(msg, ChatCompletionMessage):
                content = [{"text": msg.content}]
                if msg.role == "system":
                    system_message = content
                else:
                    message_list.append({"role": msg.role, "content": content})
            else:
                if "tool_calls" in msg:
                    tool_calls = msg["tool_calls"]
                    tool_call: ChatCompletionMessageToolCall = tool_calls[0]
                    tool_content = {
                        "toolUse": {
                            "toolUseId": tool_call.id,
                            "name": tool_call.function.name,
                            "input": json.loads(tool_call.function.arguments),
                        }
                    }
                    message_list.append(
                        {"role": msg["role"], "content": [tool_content]}
                    )
                elif "tool_call_id" in msg:
                    tool_result_content = {
                        "toolResult": {
                            "toolUseId": msg["tool_call_id"],
                            "content": [{"json": {"result": msg["content"]}}],
                        }
                    }
                    # Member must satisfy enum value set: [user, assistant]
                    message_list.append(
                        {
                            "role": "user",
                            "content": [tool_result_content],
                        }
                    )

                else:
                    content = [{"text": msg["content"]}]
                    if msg["role"] == "system":
                        system_message = content
                    else:
                        message_list.append({"role": msg["role"], "content": content})

        while len(message_list) > 0 and message_list[0]["role"] != "user":
            message_list.pop(0)

        tool_list = convert_to_tool_list(tools)

        # rich.get_console().print(message_list)
        response = self._boto3_client.converse(
            modelId=self.model_id,
            messages=message_list,
            system=system_message,
            inferenceConfig=self.inference_config,
            toolConfig={"tools": tool_list},
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
            response_to_message_chat(response=response),
            self.total_price,
        )


def response_to_message_chat(response) -> ChatCompletionMessage:
    chat_message = ChatCompletionMessage(
        role="assistant",
    )
    if "toolUse" in response["output"]["message"]["content"][0]:
        tool = response["output"]["message"]["content"][0]["toolUse"]
        chat_message.tool_calls = [
            ChatCompletionMessageToolCall(
                id=tool["toolUseId"],
                type="function",
                function=Function(
                    name=tool["name"], arguments=json.dumps(tool["input"])
                ),
            )
        ]

    if "text" in response["output"]["message"]["content"][0]:
        chat_message.content = response["output"]["message"]["content"][0]["text"]

    return chat_message


def convert_to_tool_list(params: Iterable[ChatCompletionToolParam]) -> list:
    tool_list = []
    for param in params:
        # import rich

        # rich.print(param)
        func: FunctionDefinition = param["function"]
        tool_entry = {
            "toolSpec": {
                "name": func.name,
                "description": func.description,
                "inputSchema": {"json": func.parameters},
            }
        }
        tool_list.append(tool_entry)
    return tool_list


def calculate_llm_price(
    input_tokens, output_tokens, price_per_1000_input, price_per_1000_output
):
    # Convert token counts to thousands and multiply by respective rates
    input_cost = (input_tokens / 1000) * price_per_1000_input
    output_cost = (output_tokens / 1000) * price_per_1000_output
    total_cost = input_cost + output_cost
    return total_cost
