import boto3
from botocore.exceptions import ClientError
import os
from rich.console import Console

from dotenv import load_dotenv

load_dotenv()


# Llama 3.2 Instruct (90B) pricing
price_per_1000_input = 0.002  # $0.002 per 1000 input tokens
price_per_1000_output = 0.002  # $0.002 per 1000 output tokens
console = Console()


class BedRockClient:
    def __init__(self):
        # reference: https://community.aws/content/2hHgVE7Lz6Jj1vFv39zSzzlCilG/getting-started-with-the-amazon-bedrock-converse-api?lang=en
        self.model_id = "us.meta.llama3-2-90b-instruct-v1:0"
        self.inference_config = {"maxTokens": 512, "temperature": 0.2}
        session = boto3.Session()
        self.client = session.client(
            "bedrock-runtime",
            region_name=os.getenv("AWS_REGION_NAME"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        self.total_price = 0

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
            price_per_1000_input,
            price_per_1000_output,
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
