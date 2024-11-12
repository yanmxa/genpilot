import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import BedRockClient, GroqClient
from tool import wikipedia, code_executor
from agent import DefaultAgent, Agent
from client.config import ClientConfig

from dotenv import load_dotenv

load_dotenv()


groq_client = GroqClient(
    ClientConfig(
        model="llama3-70b-8192", temperature=0.2, api_key=os.getenv("GROQ_API_KEY")
    )
)
bedrock_client = BedRockClient(
    ClientConfig(
        model="us.meta.llama3-2-90b-instruct-v1:0",
        price_1k_token_in=0.002,  # $0.002 per 1000 input tokens
        price_1k_token_out=0.002,
        ext={"inference_config": {"maxTokens": 2000, "temperature": 0.2}},
    )
)

if __name__ == "__main__":
    prompt = sys.argv[1]
    asyncio.run(
        Agent(
            client=bedrock_client,
            name="Assistant AI",
            system="You are an assistant to solve tasks, Before give a tool or function action, please give a assistant response to show your thought about it",
            tools=[wikipedia, code_executor],
        ).run(prompt)
    )
