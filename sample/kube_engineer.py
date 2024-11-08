import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agent import Agent, PromptAgent, FINAL_ANSWER
from client import GroqClient, BedRockClient, ClientConfig
from tool import code_executor
from memory import ChatBufferMemory

from dotenv import load_dotenv

load_dotenv()


groq_client = GroqClient(
    ClientConfig(
        # model="llama-3.2-90b-vision-preview",
        # model="llama-3.1-70b-versatile",
        model="llama3-70b-8192",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY"),
    )
)


engineer = Agent(
    name="Engineer",
    client=groq_client,
    tools=[code_executor],
    max_iter=20,
    is_terminal=(lambda content: content is not None and FINAL_ANSWER in content),
    memory=ChatBufferMemory(size=20),
    system=f"""
You are a Kubernetes Engineer.

## Objective:

Using code_executor tool to run code blocks to interact with Kubernetes cluster.

- Direct Command Execution: If the user provides a kubectl command or code block, execute it directly by the code_executor, and return the result.

- Handling Tasks and Issues: If the user describes a task or issue, break it into actionable steps for Kubernetes resources. Translate these steps into the appropriate kubectl commands, execute them with code_executor, and evaluate the results.

- Multi-Step Issue Resolution: For issues requiring multiple steps:

  1. Create a structured plan outlining each required step.
  2. Execute each step in sequence, verifying the outcome after each.
    - If resolved: Summarize the workflow and result.
    - If unresolved: Document progress and move to the next step.

- Unresolved Issues: If the issue remains unresolved after two rounds of the plan, summarize your findings and conclude that no further solutions are available.

## Note
 
- Always ensure the code block or command has correct syntax. If needed, make adjustments to correct it! For example, ensure that double quotes and single quotes in the code appear in pairs.

- To execute code, **use the code_executor tool** instead of embedding code blocks within the conversation. For example, **do not** wrap code like '<function=code_executor>{{"language": "bash", "code": "kubectl ..."}}<function>' in the content. Instead, call the code_executor tool directly to process the code or command.

- Do not just display the code. Instead, use the `code_executor` tool to execute the code.

Please add '{FINAL_ANSWER}' in the final answer, once the task is complete or no other action need to apply!

""",
)


# if __name__ == "__main__":
#     prompt = sys.argv[1]
#     asyncio.run(engineer.run(prompt))
