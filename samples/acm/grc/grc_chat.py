import asyncio
import sys

from genpilot.agent import Agent
from genpilot.chat import TerminalChat

from dotenv import load_dotenv

load_dotenv()

import logging

logging.basicConfig(level=logging.WARNING)

from genpilot.abc.agent import ActionPermission
from samples.acm.grc.grc_prompt import (
    GRC_AUTHOR_PROMPT,
    GRC_CRITIC_PROMPT,
    GRC_EVALUATOR_PROMPT,
    KUBERNETES_ENGINEER_PROMPT,
)

model_config = {
    "name": "groq/llama-3.3-70b-versatile",
    "config": {"temperature": 0, "stream": False},
}
terminal = TerminalChat()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    evaluator = Agent(
        name="Evaluator",
        chat=terminal,
        model_config=model_config,
        description="I am the Evaluator responsible for scoring the policy.",
        system=GRC_EVALUATOR_PROMPT.format(
            content="The initial score is 60, increasing by 20 each time, with a maximum limit of 100."
        ),  # the temporary scoring rule
        action_permission=ActionPermission.NONE,
        human_on_loop=False,
    )

    critic = Agent(
        name="Critic",
        chat=terminal,
        model_config=model_config,
        description="I am the Critic, providing suggestions to refine your policy and minimize flaws.",
        system=GRC_CRITIC_PROMPT,
        action_permission=ActionPermission.NONE,
        human_on_loop=False,
    )

    engineer = Agent(
        name="Kubernetes Engineer",
        chat=terminal,
        model_config=model_config,
        description="I am the Kubernetes Engineer to apply your eligible to the cluster",
        system=KUBERNETES_ENGINEER_PROMPT,
        mcp_server_config=sys.argv[1],
        action_permission=ActionPermission.ALWAYS,
        human_on_loop=False,
    )

    author = Agent(
        name="Author",
        chat=terminal,
        model_config=model_config,
        system=GRC_AUTHOR_PROMPT.format(
            point="80"
        ),  # the point for the author the deliver the eligible policy
        action_permission=ActionPermission.NONE,
        human_on_loop=True,
        handoffs=[evaluator, critic, engineer],
        # terminal_func=None,
    )

    try:
        await engineer.connect_to_mcp_server()
        await author.chatbot()
    finally:
        await engineer.cleanup()


# Create an ACM policy to create a namespace called lightspeed in my cluster
if __name__ == "__main__":
    asyncio.run(main())
