import os
import sys
import asyncio
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import BedRockClient, GroqClient
from tool import wikipedia, execute_code
from agent import DefaultAgent, Agent
from agent.prompt_agent import PromptAgent


def llama32_90b_client():
    return BedRockClient(
        "us.meta.llama3-2-90b-instruct-v1:0",
        {"maxTokens": 2000, "temperature": 0.2},
        0.002,
        0.002,
    )


def get_weather(location, time="now"):
    """Get the current weather in a given location. Location MUST be a city."""
    return json.dumps({"location": location, "temperature": "65", "time": time})


weather_observer = PromptAgent(
    name="Weather Observer",
    client=llama32_90b_client(),
    system=f"""Your role focuses on retrieving and analyzing current weather conditions for a specified city. Your Responsibilities: 1. Use the weather tool to find temperature, and other relevant weather data. 2. Provide updates on weather changes and forecasts.""",
    tools=[get_weather],
)


advisor = PromptAgent(
    client=llama32_90b_client(),
    name="Local Advisor",
    system=f"""Your role specializes in understanding local fashion trends and cultural influences to recommend suitable clothing.""",
    tools=[],
)


def transfer_to_weather_observer(message: str):
    """Call this function if a user is asking about current weather conditions for a specified city."""
    return weather_observer


def transfer_to_local_advisor(message: str):
    """Call this function if you want to understanding a local fashion trends and cultural influences to recommend suitable clothing."""
    return advisor


traveller = PromptAgent(
    client=llama32_90b_client(),
    name="Traveller",
    system=f"""This managerial role combines insights from both the Weather Observer and the Fashion and Culture Advisor to recommend appropriate clothing choices. Your response should be brief and to the point""",
    tools=[transfer_to_weather_observer, transfer_to_local_advisor],
    max_iter=30,
)

if __name__ == "__main__":
    asyncio.run(traveller.run("I want to go Xi 'an. What should I wear tomorrow?"))
