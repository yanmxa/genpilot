import boto3
from botocore.exceptions import ClientError
import os

from dotenv import load_dotenv

load_dotenv()


class BedRockClient:
    def __init__(self):
        self.model_id = "us.meta.llama3-2-90b-instruct-v1:0"
        self.inference_config = {"maxTokens": 512, "temperature": 0.2}
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
        return response["output"]["message"]["content"][0]["text"]
