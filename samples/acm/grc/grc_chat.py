import asyncio
import sys
from typing import Literal
from dataclasses import dataclass

from agents import (
    Agent,
    Runner,
    RunConfig,
    RunContextWrapper,
    TResponseInputItem,
    trace,
    ItemHelpers,
)


from samples.acm.grc.grc_prompt import (
    GRC_AUTHOR_PROMPT,
    GRC_CRITIC_PROMPT,
    GRC_EVALUATOR_PROMPT,
    KUBERNETES_ENGINEER_PROMPT,
)

from dotenv import load_dotenv
from genpilot.mcp.manager import MCPServerManager
from samples.acm.grc.grc_hook import EvaluationFeedback, GrcAgentHooks

load_dotenv()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_mcp_server>")
        sys.exit(1)

    async with MCPServerManager(sys.argv[1]) as server_manager:
        mcp_server_tools = await server_manager.function_tools()

        engineer = Agent(
            name="Kubernetes Engineer",
            handoff_description="I am the Engineer can apply your policy into the environment",
            instructions=KUBERNETES_ENGINEER_PROMPT,
            tools=mcp_server_tools,
            hooks=GrcAgentHooks("Engineer"),
        )
        # result = await Runner.run(agent, "List all the kubernetes clusters")
        # print(result.final_output)

        msg = input("What kind of policy would you like? \n")
        input_items: list[TResponseInputItem] = [{"content": msg, "role": "user"}]

        latest_grc: str | None = None

        critic = Agent(
            name="Critic",
            instructions=GRC_CRITIC_PROMPT,
            output_type=EvaluationFeedback,
            hooks=GrcAgentHooks("Critic"),
        )

        author = Agent(
            name="Author",
            instructions=GRC_AUTHOR_PROMPT,  # the point for the author the deliver the eligible policy
            hooks=GrcAgentHooks("Author"),
        )

        # generate the grc
        while True:
            grc_result = await Runner.run(
                author,
                input_items,
            )

            input_items = grc_result.to_input_list()
            latest_grc = ItemHelpers.text_message_outputs(grc_result.new_items)
            print("Policy generated")

            evaluator_result = await Runner.run(critic, input_items)
            result: EvaluationFeedback = evaluator_result.final_output

            print(f"Evaluator score: {result.score}")

            if result.score == "pass":
                print("GRC is good enough, exiting.")
                break

            print("Re-running with feedback")

            input_items.append(
                {"content": f"Feedback: {result.feedback}", "role": "user"}
            )

        # apply the grc
        msg = f"Please apply the following Policy into the kubernetes cluster: \n {latest_grc}"
        input_items: list[TResponseInputItem] = [{"content": msg, "role": "user"}]

        engineer_result = ""
        while True:
            engineer_result = await Runner.run(engineer, input_items)
            input_items = engineer_result.to_input_list()

            input_items.append(
                {"content": f"{engineer_result.new_items}", "role": "user"}
            )
            print()
            user_input = input("Continue? (yes/no): ").strip().lower()

            if user_input in ["no", "n"]:
                break
            if user_input in ["yes", "y"]:
                continue
            input_items.append({"content": f"User Input: {user_input}", "role": "user"})

        print(f"Input Items:\n {input_items}")
        print(f"Engineer Result:\n {engineer_result.to_input_list()}")


# Create an ACM policy to create a namespace called lightspeed in my cluster
if __name__ == "__main__":
    asyncio.run(main())

"""
$ python samples/mcp/agent.py ./samples/mcp/assistant-server-config.json

> "Create an ACM policy to create a namespace called lightspeed in my cluster"

"""
