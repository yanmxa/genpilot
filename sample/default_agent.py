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

Agent(
    client=GroqClient(
        ClientConfig(
            model="llama3-70b-8192",
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
    # chat_console=StreamlitChat("Assistant AI"),
).run("plot the tesla and apple's stock of the last year")
