from typing import Union, Tuple
import os
import sys
import json

from tool import add_agent_info, wikipedia
from client import Client
from tool.code_executor import execute_code
from .validate import StatusCode, check

current_dir = os.path.dirname(os.path.realpath(__file__))

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.pretty import Pretty
from rich.prompt import Prompt

console = Console()


class Agent:

    def __init__(
        self, client, name, description, tools=[], debug=False, grant_tool=True
    ):
        self._max_iter = 6
        self._tool = grant_tool
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
            elif status == StatusCode.ANSWER:
                #TODO: ending
                break
            else:  # Error, INVALID_JSON
                #TODO: error handling
                break
            i += 1

    def _execute(self):
        ret = self.client(self.messages)
        # https://platform.openai.com/docs/guides/chat-completions/overview
        self.messages.append({"role": "assistant", "content": ret})

        status, thought, next = check(ret)
        if (
            status == StatusCode.NONE
            or status == StatusCode.INVALID_JSON
            or status == StatusCode.ERROR
        ):
            console.print(f"{next}", style="bold red")
            console.print(ret)

            # # NOTE: Let it adjust its response; this issue occurs more frequently in the less effective model.
            # self.messages.append(
            #     {
            #         "role": "user",
            #         "content": f"{next}",
            #     }
            # )
            # return StatusCode.ACTION
            return status

        # thinking
        console.rule("🤖  " + self.name, style="dim")
        console.print()
        for item in thought:
            console.print(item)
        console.print()

        if status == StatusCode.ACTION:
            action = next
            func = action["name"]
            args = action["args"]

            # tool
            tool_info = f"🛠  [yellow]{func}[/yellow] - {args}"
            code_syntax = None
            if func == "execute_code":
                tool_info = f"🛠  [yellow]{args['language']}[/yellow]"
                code_syntax = Syntax(
                    args["code"], args["language"], theme="monokai", line_numbers=True
                )

            # Print tool info only if the tool is not set or if permission is granted
            if not self.get_execution_permission(tool_info, code_syntax):
                return

            # obs
            if func == "execute_code":
                observation = execute_code(args["language"], args["code"])
            else:
                observation = eval(f"{func}(**args)")
            console.print(f"{observation}\n", style="italic dim")

            self.messages.append(
                {
                    "role": "user",
                    "content": f"the result of action: {observation}",
                }
            )
        elif status == StatusCode.ANSWER:
            answer = next
            console.print(f"✨ {answer} \n", style="bold green")
            
            user_input = Prompt.ask("Enter prompt or '[red]exit[/red]' to quit").strip().lower()
            if user_input == "exit":
                console.print("[bold red]Goodbye![/bold red]\n")
            else:
                self.messages.append({"role": "user","content": f"{user_input}"})
                # convert the user input into an action
                return StatusCode.ACTION

        return status

    def get_execution_permission(self, tool_info, code_syntax=None):
        if code_syntax:
            console.print(code_syntax)
            console.print()
        if not self._tool:
            console.print(tool_info)
            return True

        while True:
            proceed = console.input(f"{tool_info}  👉 [dim]Y/N: [/dim]").strip().upper()
            if proceed == "Y":
                console.print()
                return True
            elif proceed == "N":
                console.print("🚫 Action cancelled by the user.\n", style="red")
                return False
            else:
                console.print(
                    "⚠️ Invalid input! Please enter 'Y' or 'N'.\n", style="yellow"
                )
