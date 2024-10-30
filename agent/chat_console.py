from typing import List
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)
import rich
import rich.rule
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.text import Text

from tool import ActionPermission

console = rich.get_console()


class ChatConsole:
    def __init__(self, name="AgentConsole"):
        self.name = name

    def system(self, str) -> None:
        # console.print(Markdown(str))
        pass

    def thinking(self, messages):
        console.rule("🤖", characters="~", style="dim")
        # console.print(messages)

    def observation(self, message):
        console.print(f"{message}\n", style="italic dim")

    def check_observation(self, obs: ChatCompletionMessageParam, max_size):
        if len(obs.get("content")) > max_size:
            input = (
                Prompt.ask(
                    "🤔 [dim]Enter[/dim] [green]o[/green]kay, [green]s[/green]hort[dim] or prompt[/dim]"
                )
                .strip()
                .lower()
            )
            if input in ["o", "okay"]:
                return obs
            elif input in ["s", "short"]:
                return ChatCompletionUserMessageParam(
                    role="user",
                    content="Observation too large to display, but successful—continue to the next step!",
                )
            else:
                return ChatCompletionUserMessageParam(role="user", content=f"{input}")

    def ask_input(self) -> str:
        input = (
            Prompt.ask("🧘 [dim]Enter[/dim] [red]exit[/red][dim] or prompt[/dim]")
            .strip()
            .lower()
        )
        print()
        if input in {"exit", "e"}:
            console.print("👋 [blue]Goodbye![/blue] \n")
            return None
        else:
            return input

    def answer(self, result):
        console.print(f"✨ {result} \n", style="bold green")

    def thought(self, result):
        console.print(f"💭 {result} \n", style="blue")

    def error(self, message):
        console.print(f"🐞 {message} \n", style="red")

    def overload(self, max_iter):
        console.print(f"💣 [red]Reached maximum iterations: {max_iter}![/red]\n")

    def check_action(self, permission, func_name, func_args, func_edit=0):
        tool_info = f"🛠  [yellow]{func_name}[/yellow] - {func_args}"
        if func_name == "execute_code":
            console.print(
                Syntax(
                    func_args["code"],
                    func_args["language"],
                    theme="monokai",
                    line_numbers=True,
                )
            )
            rich.print()
            tool_info = f"🛠  [yellow]{func_args['language']}[/yellow]"

        if permission == ActionPermission.NONE:
            console.print(tool_info)
            return True

        if permission == ActionPermission.AUTO and func_edit == 0:  # enable auto
            console.print(tool_info)
            return True

        while True:
            proceed = console.input(f"{tool_info}  👉 [dim]Y/N: [/dim]").strip().upper()
            rich.print()
            if proceed == "Y":
                return True
            elif proceed == "N":
                console.print(f"🚫 Action is canceled by user \n", style="red")
                return False
            else:
                console.print(
                    "⚠️ Invalid input! Please enter 'Y' or 'N'.\n", style="yellow"
                )
