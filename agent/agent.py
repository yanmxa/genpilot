from typing import Union, Tuple
import os
import sys
import datetime

from tool import add_agent_info, Permission, execute_code, extract_function_info
from client import GroqClient
from .validate import StatusCode, check

current_dir = os.path.dirname(os.path.realpath(__file__))

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.prompt import Prompt
import importlib
import inspect

console = Console()


class Agent:

    def __init__(
        self,
        client,
        name,
        description,
        tools=[],
        debug=False,
        permission=Permission.ALWAYS,
    ):
        self._max_iter = 6
        self._permission = permission
        self.client = client
        self.functions = {}

        self.name = name
        self.role_description = description
        self.system = self.register(tools)
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
            elif status == StatusCode.ACTION_FORBIDDEN or status == StatusCode.ANSWER:
                return
            else:  # ERROR, INVALID_JSON
                console.print("💣 [bold red]Error Caught![/bold red]\n")
                return
            i += 1
        console.print("[red]Reached maximum of {self._max_iter} iterations![/red]\n")

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
        if thought:
            for item in thought:
                console.print(item)
            console.print()

        if status == StatusCode.ACTION:
            action = next
            func_name = action["name"]
            args = action["args"]
            edit = action["edit"]

            # not register -> next
            if not func_name in self.functions:
                console.print(
                    f"[yellow]The func: {func_name} isn't registered![/yellow]\n"
                )
                console.print(action)
                self.messages.append(
                    {
                        "role": "user",
                        "content": f"not found {func_name} in available tools",
                    }
                )
                return StatusCode.ACTION

            # not allow -> exit
            if not self.get_execution_permission(func_name, args, edit):
                return StatusCode.ACTION_FORBIDDEN

            # observation -> next
            module_name = self.functions[func_name]
            if module_name not in globals():
                globals()[module_name] = importlib.import_module(module_name)
            func = getattr(sys.modules[module_name], func_name)
            observation = func(**args)

            console.print(f"{observation}\n", style="italic dim")
            self.messages.append(
                {
                    "role": "user",
                    "content": f"the result of action: {observation}",
                }
            )
            return StatusCode.ACTION
        elif status == StatusCode.ANSWER:
            answer = next
            console.print(f"✨ {answer} \n", style="bold green")

            user_input = (
                Prompt.ask("Enter prompt or '[red]exit[/red]' to quit").strip().lower()
            )
            if user_input == "exit":
                console.print("[bold red]Goodbye![/bold red]\n")
                return StatusCode.ANSWER
            else:
                self.messages.append({"role": "user", "content": f"{user_input}"})
                return StatusCode.ACTION

    def register(self, tools) -> str:
        with open(os.path.join(current_dir, "..", "prompt", "agent.md"), "r") as f:
            agent_info = f.read()

        agent_info = agent_info.replace(
            "{{time}}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        agent_info = agent_info.replace("{{name}}", self.name)
        agent_info = agent_info.replace("{{role_description}}", self.role_description)

        self.functions = {}
        tools_info = ["## Tools available:\n"]
        for tool in tools:
            module_name, func_name, params, doc = extract_function_info(tool)
            tool_md = f"### {func_name}\n"
            tool_md += f"**Parameters**: {', '.join(params)}\n\n"
            tool_md += f"**Description**:\n\n{doc}\n"
            tools_info.append(tool_md)
            self.functions[func_name] = module_name
        if len(tools) == 0:
            tools_info.append("### No tools are available")
        agent_info = agent_info + "\n".join(tools_info)
        return agent_info

    def get_execution_permission(self, func, args, edit):
        tool_info = f"🛠  [yellow]{func}[/yellow] - {args}"
        if func == "execute_code":
            tool_info = f"🛠  [yellow]{args['language']}[/yellow]"
            console.print(
                Syntax(
                    args["code"], args["language"], theme="monokai", line_numbers=True
                )
            )
            edit = 1  # always request permission for code executor
            console.print()

        if self._permission == Permission.NONE:
            console.print(tool_info)
            return True

        if self._permission == Permission.AUTO and edit == 0:
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
