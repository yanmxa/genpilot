import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import BedRockClient, GroqClient
from tool import wikipedia, code_executor, google
from agent import Agent
from agent.chat.streamlit_chat import StreamlitChat
from client.config import ClientConfig

from dotenv import load_dotenv

load_dotenv()

StreamlitChat.context(
    {
        "page_title": "AgentChat",
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

if not StreamlitChat.is_init_session():
    StreamlitChat.init_session(
        Agent(
            client=GroqClient(
                ClientConfig(
                    model="llama-3.3-70b-versatile",
                    temperature=0.2,
                    api_key=os.getenv("GROQ_API_KEY"),
                )
            ),
            name="Assistant AI",
            system="""You are an assistant to solve tasks, Before give a tool or function action, please give a assistant response to show your thought about it.
            1. If it is a code block, use the 'code_executor' tool!
            2. If it is a question, try to use the google search as soon as possible!
            
            Try to make your answer clearly and easy to read!
            """,
            tools=[google, code_executor],
            chat_console=StreamlitChat("Assistant AI"),
        )
    )

StreamlitChat.input_message()
