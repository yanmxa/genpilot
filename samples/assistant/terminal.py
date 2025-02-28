import asyncio
import os
import sys


import genpilot as gp
from genpilot.tools.code_executor import code_executor

from dotenv import load_dotenv

from samples.assistant.serper import google

load_dotenv()

terminal = gp.TerminalChat()

terminal_assistant = gp.Agent(
    name="Assistant",
    model_config={
        "name": "groq/llama-3.3-70b-versatile",
        "config": {"temperature": 0.2, "stream": False},
    },
    chat=terminal,
    tools=[code_executor, google],
    system=""""
    You are an assistant designed to help developers solve tasks in the terminal. 
    
    You can use the code_executor tool, which allows you to execute code snippets, or run commands to invoke macOS applications. If the code block runs failed, try to fix it(no packages, you can try to fix it)!
    
    You can also use the google tool search the task which answer might on the online website or internet
    
    Sample 1: Open the openshift console from the terminal

      Step 1. Retrieve the Console Route:

      - Tool Call 1: Execute `oc get route -A | grep console` using code_executor.
      - Then get the `<host-url>` from Tool Call 1 and go to step 2.

      Step 2. Open the Console:

      - Tool Call 2: Run `open <host-url>` using `code_executor` to launch the OpenShift console in your default web browser.
      - Note: Ensure that <host-url> is the one retrieved from Step 1 and not an arbitrary or imaginary URL.

    Sample 1 Completed
    """,
)


if __name__ == "__main__":
    asyncio.run(terminal_assistant.chatbot())
