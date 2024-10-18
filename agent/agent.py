from typing import Union, Tuple
import os
import sys
import json

from tool import add_agent_info, wikipedia
from client import Client

current_dir = os.path.dirname(os.path.realpath(__file__))

from rich.console import Console
from rich.markdown import Markdown
from rich import print
from rich.panel import Panel


console = Console()


class Agent:

    def __init__(self, client, name, description, tools=[], debug=False):
        self._max_iter = 6
        self.client = client

        self.name = name
        self.system = add_agent_info(
            os.path.join(current_dir, "..", "prompt", "agent.md"),
            name,
            description,
            tools,
        )
        self.debug = debug
        # if debug:
        #     console.print(Markdown(self.system))
        self.messages = [{"role": "system", "content": self.system}]

    def __call__(self, message: Union[str, Tuple[str, str]]):
        if message:
            if isinstance(message, str):
                self.messages.append({"role": "user", "content": message})
            elif isinstance(message, tuple) and len(message) == 2:
                name, msg = message
                self.messages.append({"role": "user", "name": name, "content": msg})

        i = 0
        while i < self._max_iter:
            if i == 0 or status == StatusCode.ACTION:
                status = self._execute()
            else:
                break
            i += 1

    def _execute(self):
        ret = self.client(self.messages)
        # https://platform.openai.com/docs/guides/chat-completions/overview
        self.messages.append({"role": "assistant", "content": ret})

        status = check(ret)
        if status == StatusCode.NONE or status == StatusCode.INVALID_JSON:
            return status

        obj = json.loads(ret)

        # if self.debug:
        #     console.print_json(ret)

        print(
            ":vampire:", f"""[bold magenta]{" ".join(obj["thought"])}[/bold magenta]"""
        )

        obj = json.loads(ret)
        if status == StatusCode.ACTION:
            action = obj["action"]
            func = action["name"]
            args = action["args"]

            formatted_args = ", ".join(
                f"{key} = '{value}'" for key, value in args.items()
            )
            console.print(f"Tool: {func}({formatted_args})", style="bold yellow")

            # TODO: add permission for the action
            observation = eval(f"{func}(**args)")
            print(Panel(observation))
            self.messages.append(
                {
                    "role": "user",
                    "content": f"the action observation: {observation}",
                }
            )
        elif status == StatusCode.ANSWER:
            console.print(obj["answer"], style="bold green")
            answer = obj["answer"]
            self.messages.append(
                {"role": "assistant", "content": f"the answer: {answer}"}
            )

        return status


from enum import Enum


class StatusCode(Enum):
    ACTION = 400  # Only action exists
    ANSWER = 401  # Only answer exists
    NONE = 404  # Neither action nor answer exists
    INVALID_JSON = 500  # Error: Invalid JSON


def check(input_string):
    try:
        data = json.loads(input_string)

        has_action = "action" in data and data["action"] is not None
        has_answer = "answer" in data and data["answer"] is not None
        has_thought = "thought" in data and data["thought"] is not None

        if not has_thought:
            raise ValueError("No thought provided.")
        if has_action and has_answer:
            raise ValueError("Conflict: both action and answer exist.")
        if not has_action and not has_answer:
            raise ValueError("No action or answer provided.")
        if has_action:
            action = data["action"]
            has_func = "name" in action and action is not None
            has_args = "args" in action and action is not None
            if not has_func or not has_args:
                raise ValueError("No name or args provided in action")
            return StatusCode.ACTION
        if has_answer:
            return StatusCode.ANSWER

        # Default return if none of the cases match (shouldn't occur)
        return StatusCode.NONE

    except json.JSONDecodeError as e:
        console.print(f"Invalid JSON: {input_string}. Error: {e}", style="bold red")
        return StatusCode.INVALID_JSON
    except ValueError as e:
        console.print(f"Error: {e}", style="bold red")
        return StatusCode.NONE
