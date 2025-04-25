# import os
# import sys
# import asyncio
# import json


# import genpilot as gp
# from genpilot.chat import ChainlitChat
# from genpilot.agent import Agent


# import chainlit as cl
# import rich

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
# from dotenv import load_dotenv

# load_dotenv()

# rprint = rich.get_console().print
# rprint("init context")


# # consider make an endpoint agent for the on_chat_start
# @cl.on_chat_start
# async def init_session():
#     # model_options: https://platform.openai.com/docs/api-reference/chat/create
#     chat = ChainlitChat(model_options={"temperature": 0.2, "stream": True})
#     rprint("hello session", cl.user_session.get("id"))

#     def get_weather(location, time="now"):
#         """Get the current weather in a given location. Location MUST be a city."""
#         return json.dumps({"location": location, "temperature": "65", "time": time})

#     weather_observer = gp.Agent(
#         name="Weather Observer",
#         model="groq/llama-3.3-70b-versatile",
#         chat=chat,
#         tools=[get_weather],
#         system="Your role focuses on retrieving and analyzing current weather conditions for a specified city. Your Responsibilities: Use the weather tool to find temperature. Typically, you only call the tool once and return the result. Do not call the weather with same input many times",
#     )

#     advisor = gp.Agent(
#         name="Local Advisor",
#         model="groq/llama-3.3-70b-versatile",
#         chat=chat,
#         system="Your role specializes in understanding local fashion trends and cultural influences to recommend suitable clothing.",
#     )

#     def transfer_to_weather_observer(message: str) -> gp.IAgent:
#         """Call this function if a user is asking about current weather conditions for a specified city."""
#         return weather_observer

#     def transfer_to_local_advisor(message: str) -> gp.IAgent:
#         """Call this function if you want to understanding a local fashion trends and cultural influences to recommend suitable clothing."""
#         return advisor

#     traveller = gp.Agent(
#         name="Traveller",
#         model="groq/llama-3.3-70b-versatile",
#         chat=chat,
#         tools=[transfer_to_weather_observer, transfer_to_local_advisor],
#         system="This managerial role combines insights from both the Weather Observer and the Fashion and Culture Advisor to recommend appropriate clothing choices. Once you have the information for both Observer and Advisor. You can summarize give the final response. The final response with concise, straightforward items, like 1,2,3..",
#         max_iter=10,
#         memory=gp.memory.BufferMemory(30),
#     )

#     cl.user_session.set("traveller", traveller)

#     rprint("session init traveller")


# @cl.on_chat_end
# def end():
#     rprint("session goodbye", cl.user_session.get("id"))


# @cl.on_message
# async def main(message: cl.Message):
#     rprint("on message")

#     result = asyncio.run(message.send())
#     rprint(f"sent result on message: {result}")

#     traveller = cl.user_session.get("traveller")

#     result = traveller.run(message.content)

#     rprint(f"traveller result on message: {result}")
