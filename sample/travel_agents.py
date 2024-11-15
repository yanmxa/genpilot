import os
import sys
import asyncio
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import BedRockClient, GroqClient, ClientConfig
from tool import wikipedia, code_executor
from agent import DefaultAgent, Agent, PromptAgent, FINAL_ANSWER
from memory import ChatBufferMemory, ChatVectorMemory
from dotenv import load_dotenv
from agent.agent import IAgent

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
        model="llama3-70b-8192", temperature=0.2, api_key=os.getenv("GROQ_API_KEY")
    )
)


def get_weather(location, time="now"):
    """Get the current weather in a given location. Location MUST be a city."""
    return json.dumps({"location": location, "temperature": "65", "time": time})


weather_observer = Agent(
    name="Weather Observer",
    client=groq_client,
    system=f"""Your role focuses on retrieving and analyzing current weather conditions for a specified city. Your Responsibilities: 1. Use the weather tool to find temperature, and other relevant weather data. 2. Provide updates on weather changes and forecasts.
    Prefix the response with '{FINAL_ANSWER}' once the task is complete!""",
    tools=[get_weather],
)


advisor = Agent(
    client=groq_client,
    name="Local Advisor",
    system=f"""Your role specializes in understanding local fashion trends and cultural influences to recommend suitable clothing.
    Prefix the response with '{FINAL_ANSWER}' once the task is complete!""",
    tools=[],
)


def transfer_to_weather_observer(message: str) -> Agent:
    """Call this function if a user is asking about current weather conditions for a specified city."""
    return weather_observer


def transfer_to_local_advisor(message: str) -> Agent:
    """Call this function if you want to understanding a local fashion trends and cultural influences to recommend suitable clothing."""
    return advisor


traveller = Agent(
    client=groq_client,
    name="Traveller",
    system=f"""This managerial role combines insights from both the Weather Observer and the Fashion and Culture Advisor to recommend appropriate clothing choices. Once you have the information for both Observer and Advisor. You can summarize give the final response. The final response with concise, straightforward items, like 1,2,3...
    Prefix the response with '{FINAL_ANSWER}' once the task is complete!""",
    tools=[transfer_to_weather_observer, transfer_to_local_advisor],
    max_iter=10,
    memory=ChatBufferMemory(size=30),
)

if __name__ == "__main__":
    asyncio.run(traveller.run("I want to go Xi 'an tomorrow. What should I wear?"))
