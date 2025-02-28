import asyncio
import os
import sys
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from agent import Agent, PromptAgent, FINAL_ANSWER
from client import GroqClient, BedRockClient, ClientConfig
from memory import ChatBufferMemory
from tools import KubectlExecutor

from sample.globalhub.prompt import agent_prompt_template

from dotenv import load_dotenv

load_dotenv()

current_dir = os.path.dirname(os.path.realpath(__file__))

groq_client = GroqClient(
    ClientConfig(
        model="llama-3.2-90b-vision-preview",
        # model="llama-3.3-70b-versatile",
        # model="llama3-70b-8192",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY"),
    )
)

current_dir = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
    cluster_name = "demo-hub-a"
    namespace = "multicluster-global-hub-agent"
    component_name = "multicluster-global-hub-agent"

    prompt = sys.argv[1]

    cluster = KubectlExecutor.from_yaml(
        os.path.join(current_dir, "cluster-options.yaml")
    )

    global_hub_agent = Agent(
        # debug=False,
        name="GlobalHubAgent",
        client=groq_client,
        tools=[cluster.kubectl_cmd],
        max_iter=20,
        memory=ChatBufferMemory(size=30),
        system=agent_prompt_template.format(
            namespace=namespace,
            component_name=component_name,
        ),
    )
    asyncio.run(global_hub_agent.run(prompt))
