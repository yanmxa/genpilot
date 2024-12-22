import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tool import code_executor
from agent import PromptAgent
from client import BedRockClient, GroqClient, ClientConfig
from dotenv import load_dotenv
import instructor

load_dotenv()

bedrock_client = BedRockClient(
    ClientConfig(
        model="us.meta.llama3-2-90b-instruct-v1:0",
        price_1k_token_in=0.002,  # $0.002 per 1000 input tokens
        price_1k_token_out=0.002,
        ext={"inference_config": {"maxTokens": 2000, "temperature": 0.2}},
    )
)

groq_client = GroqClient(
    ClientConfig(
        model="llama3-70b-8192",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY"),
        mode=instructor.Mode.JSON,
    )
)


def main():
    prompt = sys.argv[1]
    a = PromptAgent(
        bedrock_client,
        "Assistant AI",
        "You are an assistant to solve tasks. You can use the code executor write python code to do that.",
        tools=[code_executor],
        max_iter=10,
    )
    response = a.run(prompt)


if __name__ == "__main__":
    main()
