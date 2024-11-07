import sys
from typing import List, Tuple
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
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn
import asyncio
from type import ActionPermission
from rich.console import Console
from memory import ChatMemory
from rich.markdown import Markdown


chat_console = rich.get_console()


class ChatConsole:
    def __init__(self, name="AgentConsole"):
        self.name = name

    def system(self, str) -> None:
        # console.print(Markdown(str))
        pass

    def delivery(self, from_agent, to_agent, message):
        #  title = f"📨 [bold yellow]{agent_a}[/bold yellow] [cyan]→[/cyan] [bold magenta]{agent_b}[/bold magenta]"
        title = f"📨 [bold bright_cyan]{to_agent}[/bold bright_cyan]"
        chat_console.print()

        markdown = Markdown(message)

        # f"[white]{message}[/white]"
        panel = Panel(
            markdown,
            title=title,
            subtitle=f"from {from_agent}",
            title_align="left",
            padding=(1, 2),
            border_style="bright_black",  # A softer border color
        )

        chat_console.print(panel)

    def thinking(self, messages):
        # chat_console.rule("🤖", characters="~", style="dim")
        # chat_console.print(messages)
        for msg in messages:
            chat_console.print(f"    {msg}", style="dim blue")
        chat_console.print()

    async def async_thinking(self, messages, finished_event):
        # chat_console.print(messages)
        chat_console.print()
        with Progress(SpinnerColumn(), console=Console(), transient=True) as progress:
            building_task = progress.add_task("LLM thinking", total=None)
            while not finished_event.is_set():
                elapsed_time = progress.tasks[building_task].elapsed
                await asyncio.sleep(0.1)
                # progress.advance(building_task)  # Advance the spinner
            # chat_console.print(messages)
            elapsed_time = progress.tasks[building_task].elapsed
        chat_console.print(f"[dim][+] Thinking {elapsed_time:.2f}s")
        chat_console.print()

    def price(self, value):
        if value is not None and value != "":
            clear_previous_lines()
            chat_console.print(f"[dim][$] {value}")

    def observation(self, message):
        text = Text(f"{message}")
        text.stylize("dim")
        chat_console.print(text)
        # chat_console.print(f"{message}", style="italic dim")

    def check_observation(self, obs: ChatCompletionMessageParam, max_size):
        if len(obs.get("content")) > max_size:
            chat_console.print()
            input = (
                Prompt.ask("🤔 [dim]Enter [green]s[/green]hort observation[/dim]")
                .strip()
                .lower()
            )
            clear_previous_lines(n=2)
            if input == "" or input in ["y", "yes", "okay", "ok"]:
                return obs
            elif input in ["s", "short"]:
                return ChatCompletionUserMessageParam(
                    role="user",
                    content="Observation too large to display, but successful—continue to the next step!",
                )
            elif input in ["e", "exit"]:
                return ChatCompletionUserMessageParam(
                    role="user",
                    content="Observation too large to display, but successful—continue to the next step!",
                )
            else:
                return ChatCompletionUserMessageParam(role="user", content=f"{input}")
        return obs

    def ask_input(self, system, memory: ChatMemory, tools=None) -> str:
        while True:
            user_input = (
                Prompt.ask("🧘 [dim]Enter[/dim] [red]exit[/red][dim] or prompt[/dim]")
                .strip()
                .lower()
            )
            print()
            if user_input in {"exit", "e"}:
                chat_console.print("👋 [blue]Goodbye![/blue]")
                break
            elif user_input == "/debug":  # print the whole information
                messages = memory.get(system)
                chat_console.print(messages)
                if tools:
                    chat_console.print(tools)
                continue
            elif "/memorize" in user_input or "/m" in user_input:
                input = user_input.replace("/memorize", "").replace("/m", "").strip()
                memory.add(
                    ChatCompletionUserMessageParam(content=input, role="user"),
                    persistent=True,
                )
                continue
            elif "/clear" in user_input:
                memory.clear()
                continue
            else:
                return user_input

    def answer(self, result):
        result = result.strip()
        chat_console.print(f"✨ {result} \n", style="bold green")

    def thought(self, result):
        chat_console.print(f"💭 {result} \n", style="blue")

    def error(self, message):
        chat_console.print()
        chat_console.print(f"🐞 {message} \n", style="red")

    def overload(self, max_iter):
        chat_console.print(f"💣 [red]Reached maximum iterations: {max_iter}![/red]\n")

    def check_action(self, permission, func_name, func_args, func_edit=0):
        tool_info = f"🛠  [yellow]{func_name}[/yellow] - [dim]{func_args}[/dim]"
        if func_name == "code_executor":
            chat_console.print(
                Syntax(
                    func_args["code"],
                    func_args["language"],
                    theme="monokai",
                    line_numbers=True,
                )
            )
            rich.print()
            tool_info = f"🛠  [yellow]{func_args['language']}[/yellow]"
        else:
            if len(f"{func_args}") > 20:
                args_str = f"{func_args}"[:10] + "..." + f"{func_args}"[-10:]
                tool_info = f"🛠  [yellow]{func_name}[/yellow] - [dim]{args_str}[/dim]"
        if permission == ActionPermission.NONE:
            chat_console.print(tool_info)
            return True

        if permission == ActionPermission.AUTO and func_edit == 0:  # enable auto
            chat_console.print(tool_info)
            return True

        while True:
            proceed = (
                chat_console.input(f"{tool_info}  👉 [dim]Approve ?: [/dim]")
                .strip()
                .upper()
            )
            rich.print()
            if proceed == "Y":
                return True
            elif proceed == "N":
                chat_console.print(f"🚫 Action is canceled by user \n", style="red")
                return False
            else:
                chat_console.print(
                    "⚠️ Invalid input! Please enter 'Y' or 'N'.\n", style="yellow"
                )


def clear_previous_lines(n=1):
    for _ in range(n):
        sys.stdout.write("\033[F")  # Move the cursor up one line
        sys.stdout.write("\033[K")  # Clear the line
    sys.stdout.flush()
