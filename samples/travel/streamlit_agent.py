import genpilot
import os
import sys
import asyncio
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from dotenv import load_dotenv

from genpilot.chat.streamlit_chat import StreamlitChat
from genpilot.agent.default_agent import Agent

load_dotenv()

import streamlit as st
import genpilot as gp
from genpilot.chat.streamlit_chat import StreamlitChat
from genpilot.agent.default_agent import Agent

st.set_page_config(
    **{
        "page_title": "GenPilot",
        "page_icon": "🚀",
        # "layout": "wide",
        "initial_sidebar_state": "auto",
        "menu_items": {
            "Get Help": "https://www.extremelycoolapp.com/help",
            "Report a bug": "https://www.extremelycoolapp.com/bug",
            "About": "# This is a header. This is an *extremely* cool app!",
        },
    }
)
st.markdown(
    """
  <style>
      .reportview-container {
          margin-top: -2em;
      }
      #MainMenu {visibility: hidden;}
      .stAppDeployButton {display:none;}
      footer {visibility: hidden;}
      #stDecoration {display:none;}
  </style>
""",
    unsafe_allow_html=True,
)

if "chat" not in st.session_state:
    # model_options: https://platform.openai.com/docs/api-reference/chat/create
    st.session_state.chat = StreamlitChat(
        model_options={"temperature": 0.2, "stream": False}
    )

if "traveller" not in st.session_state:

    def get_weather(location, time="now"):
        """Get the current weather in a given location. Location MUST be a city."""
        return json.dumps({"location": location, "temperature": "65", "time": time})

    weather_observer = Agent(
        name="Weather Observer",
        model="groq/llama-3.3-70b-versatile",
        chat=st.session_state.chat,
        tools=[get_weather],
        system="Your role focuses on retrieving and analyzing current weather conditions for a specified city. Your Responsibilities: Use the weather tool to find temperature. Do not call the weather with same input many times",
    )

    advisor = Agent(
        name="Local Advisor",
        model="groq/llama-3.3-70b-versatile",
        chat=st.session_state.chat,
        system="Your role specializes in understanding local fashion trends and cultural influences to recommend suitable clothing.",
    )

    def transfer_to_weather_observer(message: str) -> gp.IAgent:
        """Call this function if a user is asking about current weather conditions for a specified city."""
        return weather_observer

    def transfer_to_local_advisor(message: str) -> gp.IAgent:
        """Call this function if you want to understanding a local fashion trends and cultural influences to recommend suitable clothing."""
        return advisor

    traveller = Agent(
        name="Traveller",
        model="groq/llama-3.3-70b-versatile",
        chat=st.session_state.chat,
        tools=[transfer_to_weather_observer, transfer_to_local_advisor],
        system="This managerial role combines insights from both the Weather Observer and the Fashion and Culture Advisor to recommend appropriate clothing choices. Once you have the information for both Observer and Advisor. You can summarize give the final response. The final response with concise, straightforward items, like 1,2,3..",
        max_iter=10,
        # memory=gp.memory.BufferMemory(30),
    )
    st.session_state.traveller = traveller

# I want to go Xi 'an tomorrow. What should I wear?
res = st.session_state.traveller.run()
print("result: ", res)
