import os
import sys
import asyncio
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import BedRockClient, GroqClient
from tool import wikipedia, execute_code
from agent import DefaultAgent, Agent
from agent.prompt_agent import PromptAgent

FINAL_ANSWER = "ANSWER:"


def get_weather(location, time="now"):
    """Get the current weather in a given location. Location MUST be a city."""
    return json.dumps({"location": location, "temperature": "65", "time": time})


weather_observer = Agent(
    name="Weather Observer",
    client=GroqClient(),
    system=f"""Your role focuses on retrieving and analyzing current weather conditions for a specified city. Your Responsibilities: 1. Use the weather tool to find temperature, and other relevant weather data. 2. Provide updates on weather changes and forecasts.
    Prefix the response with '{FINAL_ANSWER}' once the task is complete!""",
    tools=[get_weather],
    standalone=False,
)


advisor = Agent(
    client=GroqClient(),
    name="Local Advisor",
    system=f"""Your role specializes in understanding local fashion trends and cultural influences to recommend suitable clothing.
    Prefix the response with '{FINAL_ANSWER}' once the task is complete!""",
    tools=[],
    standalone=False,
)


def transfer_to_observer(message: str):
    """Call this function if a user is asking about current weather conditions for a specified city."""
    return weather_observer


def transfer_to_advisor(message: str):
    """Call this function if you want to understanding a local fashion trends and cultural influences to recommend suitable clothing."""
    return advisor


manager = Agent(
    client=GroqClient(),
    name="Manager",
    system=f"""This managerial role combines insights from both the Weather Observer and the Fashion and Culture Advisor to recommend appropriate clothing choices. Your response should be brief and to the point.
    Prefix the response with '{FINAL_ANSWER}' once the task is complete!""",
    tools=[transfer_to_observer, transfer_to_advisor],
    standalone=True,
    max_iter=30,
)

if __name__ == "__main__":
    asyncio.run(manager.run("I want to go Xi 'an tomorrow. What should I wear?"))
