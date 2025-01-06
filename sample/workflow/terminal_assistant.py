import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from client import GroqClient
from tool import wikipedia, code_executor, google
from agent import Agent
from agent.chat.terminal_chat import TerminalChat
from client.config import ClientConfig

from dotenv import load_dotenv

load_dotenv()

a = Agent(
    client=GroqClient(
        ClientConfig(
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    ),
    name="Terminal Assistant AI",
    system="""
    You are an assistant designed to help developers solve tasks in the terminal. You have access to the code_executor tool, which allows you to execute code snippets and run commands to invoke macOS applications.
    
    Note: Each tool_calls from the assistant should only contain only one function/tool.
    
    Sample1: Open the openshift console from the terminal

    Sample Task 1: Open the OpenShift Console from the Terminal
    
      Step 1. Retrieve the Console Route:
      
      - Tool Call 1: Execute `oc get route -A | grep console` using code_executor.
      - Then get the `<host-url>` from Tool Call 1 and go to step 2.

      Step 2. Open the Console:
      
      - Tool Call 2: Run `open <host-url>` using `code_executor` to launch the OpenShift console in your default web browser.
      - Note: Ensure that <host-url> is the one retrieved from Step 1 and not an arbitrary or imaginary URL.
      
    Task 1 Completed
    
   """,
    tools=[code_executor],
    chat_console=TerminalChat("Terminal assistant", validate_obs=False),
)

a.chatbot()
