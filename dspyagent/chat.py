from dspy.primitives.program import Module
import sys
import re
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
from rich.padding import Padding
from agent.interface import IChat

chat_console = rich.get_console()


class ChatConsole(IChat):
    def __init__(self, name="AgentConsole"):
        self._before_thinking = False
        self.name = name

    def system(self, str) -> None:
        # console.print(Markdown(str))
        pass

    def next_speaker(self, to_agent, message):
        import json
        # Ensure the message is a string before trying to parse it as JSON
        # print(message)
        if isinstance(message, str):
            values = message   # If it's already a dict or non-string, treat as plain text
        else:
            values = "\n".join(str(value) for value in message.values())
        if len(f"{message}") > 1000:
            panel = Panel(
              Markdown(values),
              title="📩",
              # subtitle=f"from {from_agent}",
              # title_align="left",
              padding=(1, 2),
              border_style="bright_black",  # A softer border color
            )
            chat_console.print(panel)
        else:
           chat_console.print(f"📩 {values}")
        
        chat_console.print()
        from rich.rule import Rule
        chat_console.print(Rule(f"🤖 [bold green]{to_agent}[/bold green]", align="left"))
        chat_console.print()
            

    def markdown(self, content, title=None):
        markdown = Markdown(content)
        panel = Panel(
            markdown,
            title=title,
            # subtitle=f"from {from_agent}",
            # title_align="left",
            padding=(1, 2),
            border_style="bright_black",  # A softer border color
        )
        chat_console.print(panel)

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
        # chat_console.print()
        if isinstance(messages, str):
          chat_console.print(f"{messages}", style="cyan")
          chat_console.print()
          return
        for msg in messages:
            chat_console.print(f"    {msg}", style="cyan")
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
        chat_console.print(f"[dim][+] {self.name} Thinking {elapsed_time:.2f}s")
        chat_console.print()

    def price(self, value):
        if value is not None and value != "":
            clear_previous_lines()
            chat_console.print(f"[dim][$] {value}")
            chat_console.print()

    def observation(self, obs) -> str:
        """
        Must return the change obs
        """
        # obs = deduplicate_log(obs)
        text = Text(f"{obs}")
        text.stylize("dim")
        chat_console.print(Padding(text, (0, 0, 1, 3)))  # Top, Right, Bottom, Left
        # chat_console.print(text, padding=(0, 0, 0, 2))
        # chat_console.print(f"{message}", style="italic dim")
        return obs
      
    def after_tool(self, obs: str, max_size):
        if len(obs) > max_size:
            chat_console.print()
            prompt_ask = "🤔 [dim][green]A[/green]lternative[/dim]"
            try:
                input = (
                    Prompt.ask(prompt_ask).strip().lower()
                )  # Prompt for the first line
            except EOFError:
                input = ""
            if input == "paste":
                try:
                    multi_line_input = (
                        sys.stdin.read().strip().lower()
                    )  # Capture multi-line pasted input
                    input = multi_line_input
                except EOFError:
                    input = ""

            if input == "" or input in ["y", "yes", "okay", "ok"]:
                clear_previous_lines(n=2)
                return obs
            elif input in ["s", "short"]:
                return "Observation too large to display, but successful—continue to the next step!"
            elif input in ["e", "exit"]:
                return "User exit!"
            else:
                self.observation(f"{input}")
                return f"{input}"
        return obs

    def after_action(self, obs: ChatCompletionMessageParam, max_size):
        if len(obs.get("content")) > max_size:
            chat_console.print()
            prompt_ask = "🤔 [dim][green]A[/green]lternative[/dim]"
            try:
                input = (
                    Prompt.ask(prompt_ask).strip().lower()
                )  # Prompt for the first line
            except EOFError:
                input = ""
            if input == "paste":
                try:
                    multi_line_input = (
                        sys.stdin.read().strip().lower()
                    )  # Capture multi-line pasted input
                    input = multi_line_input
                except EOFError:
                    input = ""

            if input == "" or input in ["y", "yes", "okay", "ok"]:
                clear_previous_lines(n=2)
                return obs
            elif input in ["s", "short"]:
                return ChatCompletionUserMessageParam(
                    role="user",
                    content="Observation too large to display, but successful—continue to the next step!",
                )
            elif input in ["e", "exit"]:
                return ChatCompletionUserMessageParam(
                    role="user",
                    content="User exit!",
                )
            else:
                self.observation(f"{input}")
                return ChatCompletionUserMessageParam(role="user", content=f"{input}")
        return obs

    def _ask_input(
        self,
        memory: ChatMemory,
        system=None,
        tools=None,
        name=None,
        prompt_ask="🧘 [dim]Enter[/dim] [red]exit[/red][dim] or prompt[/dim]",
        skip_inputs=[],
        ignore_inputs=[""],  # Skip empty input by default
    ) -> bool:
        while True:
            # Prompt the user for input
            user_input = Prompt.ask(prompt_ask).strip().lower()
            print()

            if user_input in skip_inputs:
                return True

            if user_input in ignore_inputs:
                continue

            match user_input:
                case "exit" | "e":
                    chat_console.print("👋 [blue]Goodbye![/blue]")
                    return False

                case "/debug":
                    chat_console.print(memory.get(system))
                    continue

                case "/debug-tool":
                    if tools or len(tools) > 0:
                        chat_console.print(tools)
                    continue

                case "/pop":
                    memory.pop()
                    chat_console.print(memory.get(system))
                    continue

                case "/add" | "/a":
                    input_content = (
                        user_input.replace("/add", "").replace("/a", "").strip()
                    )
                    if input_content:
                        memory.add(
                            ChatCompletionUserMessageParam(
                                content=input_content, role="user", name=name
                            )
                        )
                    continue

                case "/clear":
                    memory.clear()
                    continue

                case _:

                    # Add the user input to memory and return it
                    memory.add(
                        ChatCompletionUserMessageParam(
                            content=user_input, role="user", name=name
                        )
                    )
                    return True

    def before_thinking(self, memory: ChatMemory, tools=[]) -> bool:
        if not self._before_thinking:
            return True
        return self._ask_input(memory, tools=tools, skip_inputs=["", "yes", "approve"])
      
    def answer(self, **input_args) -> bool:
      values = list(input_args.values())
      for i, value in enumerate(values):
          if i == len(values) - 1:  # Last value
              chat_console.print(f"✨ {value} \n", style="bold green")
          else:
              chat_console.print(f"   {value} \n", style="dim green")

    def thought(self, **input_args):
        values = list(input_args.values())
        for i, value in enumerate(values):
            if i == len(values) - 1:  # Last value
                chat_console.print(f"{value} \n", style="blue")
            else:
                chat_console.print(f"{value} \n", style="dim blue")

    def error(self, message):
        chat_console.print()
        chat_console.print(f"🐞 {message} \n", style="red")

    def overload(self, max_iter):
        chat_console.print(f"💣 [red]Reached maximum iterations: {max_iter}![/red]\n")

    def before_action(
        self, permission, func_name, func_args, func_edit=0, functions={}
    ) -> bool:
        # check the agent function
        func = functions[func_name]
        return_type = func.__annotations__.get("return")
        if return_type is not None and issubclass(return_type, IAgent):
            # TODO: add other information
            return True

        tool_info = f"🛠 [yellow]{func_name}[/yellow] - [dim]{func_args}[/dim]"
        if func_name == "code_executor":
            chat_console.print(f"🛠 [yellow]{func_args['language']}[/yellow]")
            rich.print()
            chat_console.print(
                Syntax(
                    func_args["code"],
                    func_args["language"],
                    theme="monokai",
                    line_numbers=True,
                )
            )
        elif func_name == "kubectl_cmd":
            block = func_args["command"] + func_args["input"]
            chat_console.print(
                f"🛠 [yellow] cluster: {func_args['cluster_name']}[/yellow]"
            )
            rich.print()
            chat_console.print(
                Syntax(
                    block,
                    "shell",
                    theme="monokai",
                    line_numbers=True,
                )
            )
        else:
            chat_console.print(tool_info)
        rich.print()

        if permission == ActionPermission.NONE:
            return True

        if permission == ActionPermission.AUTO and func_edit == 0:  # enable auto
            return True

        # chat_console.print(f"🛠  [yellow]{func_name}[/yellow]\n")
        # chat_console.print(f"   [dim]{func_args} [/dim] \n")
        while True:
            proceed = chat_console.input(f"👉 [dim]Approve ?: [/dim]").strip().upper()
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


    def before_tool(
        self, func_name, func_args, tool
    ) -> bool:
        # # check the agent function
        # return_type = func.__annotations__.get("return")
        if issubclass(tool.return_type, Module):
            # TODO: add other information
            # chat_console.print(f"📩 {func_args}\n")
            return True

        if func_name == "code_executor":
            chat_console.print(f"🛠 [yellow]{func_args['language']}[/yellow]")
            rich.print()
            chat_console.print(
                Syntax(
                    func_args["code"],
                    func_args["language"],
                    theme="monokai",
                    line_numbers=True,
                )
            )
        elif func_name == "kubectl_cmd":
            block = func_args["command"]
            if "input" in func_args:
                block = func_args["command"] + func_args["input"]
            chat_console.print(
                f"🛠 [yellow] cluster: {func_args['cluster_name']}[/yellow]"
            )
            rich.print()
            chat_console.print(
                Syntax(
                    block,
                    "shell",
                    theme="monokai",
                    line_numbers=True,
                )
            )
        else:
            chat_console.print(f"🛠 [yellow]{func_name}[/yellow] - [dim]{func_args}[/dim]")
        rich.print()


        # chat_console.print(f"🛠  [yellow]{func_name}[/yellow]\n")
        # chat_console.print(f"   [dim]{func_args} [/dim] \n")
        while True:
            proceed = chat_console.input(f"👉 [dim]Approve ?: [/dim]").strip().upper()
            rich.print()
            if proceed == "Y":
                return True
            elif proceed == "N":
                chat_console.print(f"🚫 Action is canceled by user \n", style="red")
                sys.exit(0)
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


def deduplicate_log(log: str, size=3000) -> str:
    """
    Deduplicate logs and only keep the latest log entries.

    Args:
        log (str): The log string containing multiple log entries.
        size (int): The maximum size of the log to process.

    Returns:
        str: Deduplicated logs with only the latest entries.
    """
    # Limit log size
    if len(log) > size:
        log = log[-size:]

    lines = log.splitlines()
    latest_logs = {}

    for line in lines:
        # Remove timestamp (common formats: YYYY-MM-DD, HH:MM:SS, or ISO8601)
        cleaned_line = re.sub(
            r"\d{4}-\d{2}-\d{2}[T ]?\d{2}:\d{2}:\d{2}(?:\.\d+Z)?", "", line
        ).strip()

        # Update the latest occurrence of each log message
        latest_logs[cleaned_line] = line  # Overwrite with the latest line

    # Return the latest entries in the order they appeared
    return "\n".join(latest_logs.values())
