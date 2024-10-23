import boto3
from botocore.exceptions import ClientError
import os
from rich.console import Console

from dotenv import load_dotenv

load_dotenv()


console = Console()


class BedRockClient:
    def __init__(
        self, model_id, inference_config, price_per_1000_input, price_per_1000_output
    ):
        # reference: https://community.aws/content/2hHgVE7Lz6Jj1vFv39zSzzlCilG/getting-started-with-the-amazon-bedrock-converse-api?lang=en
        self.model_id = model_id
        self.inference_config = inference_config
        self.price_per_1000_input = price_per_1000_input
        self.price_per_1000_output = price_per_1000_output
        self.total_price = 0

        session = boto3.Session()
        self.client = session.client(
            "bedrock-runtime",
            region_name=os.getenv("AWS_REGION_NAME"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

    def __call__(self, messages):
        message_list = []
        for msg in messages:
            content = [{"text": msg["content"]}]
            if msg["role"] == "system":
                system_message = content
            else:
                message_list.append({"role": msg["role"], "content": content})
        response = self.client.converse(
            modelId=self.model_id,
            messages=message_list,
            system=system_message,
            inferenceConfig=self.inference_config,
        )
        usage = response["usage"]
        cost = calculate_llm_price(
            usage["inputTokens"],
            usage["outputTokens"],
            self.price_per_1000_input,
            self.price_per_1000_output,
        )
        self.total_price += cost
        console.print(f"Total Cost: {self.total_price}", style="italic dim")
        return response["output"]["message"]["content"][0]["text"]


def calculate_llm_price(
    input_tokens, output_tokens, price_per_1000_input, price_per_1000_output
):
    # Convert token counts to thousands and multiply by respective rates
    input_cost = (input_tokens / 1000) * price_per_1000_input
    output_cost = (output_tokens / 1000) * price_per_1000_output
    total_cost = input_cost + output_cost
    return total_cost
