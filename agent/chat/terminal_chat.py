import sys
import re
from typing import List, Tuple
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionMessage,
)
import rich
import rich.rule
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.text import Text
from rich.panel import Panel
from type import ActionPermission
from memory import ChatMemory
from rich.markdown import Markdown
from rich.padding import Padding
import threading
from typing import Callable, Any
import time

from agent.interface.chat import IChat
from agent.interface.agent import IAgent
from .streamlit_chat import assistant_message_to_param

chat_console = rich.get_console()


class TerminalChat(IChat):
    def __init__(self, name="AgentConsole", memory=None):
        self._before_thinking = False
        self.name = name
        self.validate_obs = True
        self.memory = memory

    def system(self, str) -> None:
        # console.print(Markdown(str))
        pass

    def avatar(self):
        return "🤖"

    def input(self, message, from_agent_name="user", from_agent_avatar=None):
        #  title = f"📨 [bold yellow]{agent_a}[/bold yellow] [cyan]→[/cyan] [bold magenta]{agent_b}[/bold magenta]"
        title = f"📨 [bold bright_cyan]{self.name}[/bold bright_cyan]"
        chat_console.print()
        message = message.get("content")
        markdown = Markdown(message)

        # f"[white]{message}[/white]"validate_observation
        panel = Panel(
            markdown,
            title=title,
            subtitle=f"from {from_agent_name}",
            title_align="left",
            padding=(1, 2),
            border_style="bright_black",  # A softer border color
        )

        chat_console.print(panel)
        pass

    def assistant_thinking(
        self, task_func: Callable[..., Any], *args: Any
    ) -> ChatCompletionMessageParam:
        chat_console.print()
        # Record the start time
        start_time = time.time()
        # Create a threading event to stop the spinner when the task finishes
        stop_event = threading.Event()
        # Start the spinner in a separate thread
        spinner_thread = threading.Thread(target=spinner, args=(stop_event,))
        spinner_thread.start()
        # Run the provided task function with its arguments and capture the result
        message, price = task_func(*args)
        # Set the stop_event to stop the spinner after the task is complete
        stop_event.set()
        # Wait for the spinner thread to finish
        spinner_thread.join()
        # Calculate the elapsed time in seconds
        elapsed_time = time.time() - start_time
        # Clear the spinner from the terminal by overwriting the spinner with spaces
        sys.stdout.write("\r    \r")  # Overwrites the spinner with spaces
        sys.stdout.flush()
        chat_console.print(f"[dim][+] {self.name} Thinking {elapsed_time:.2f}s")
        if price is not None and price != "":
            chat_console.print(f"[dim][$] {price}")
        chat_console.print()
        assistant_message = assistant_message_to_param(message)
        return assistant_message

    def observation(self, obs_param, thinking=False) -> str:
        """
        Must return the change obs or thinking
        """
        # if thinking:
        #     for msg in obs:
        #         chat_console.print(f"    {msg}", style="cyan")
        #     chat_console.print()
        #     return None

        # obs = deduplicate_log(obs)
        message = obs_param.get("content")
        text = Text(f"{message}")
        text.stylize("dim")
        chat_console.print(Padding(text, (0, 0, 1, 3)))  # Top, Right, Bottom, Left
        # chat_console.print(text, padding=(0, 0, 0, 2))
        # chat_console.print(f"{message}", style="italic dim")

        if self.validate_obs:
            obs_str = self.validate_observation(obs_param)
        return obs_str

    def validate_observation(self, obs_param):
        prompt_ask = "🤔 [dim]Alternative Obs?[/dim]"
        try:
            input = Prompt.ask(prompt_ask).strip().lower()  # Prompt for the first line
        except EOFError:
            input = ""
        if input in ["s", "short", "y", "yes", "okay", "ok"]:
            self.memory.get(None)[-1][
                "content"
            ] = "Observation too large to display, but successful—continue to the next step!"
            clear_previous_lines(n=2)
            return "Observation too large to display, but successful—continue to the next step!"
        elif input in ["n", "no", ""]:
            # self.memory.get(None)[-1]["content"] = obs
            # The above code is a Python script that prints the value associated with the key
            # "content" in the dictionary `obs_param`.
            # print("print the original observation", obs_param.get("content"))
            return obs_param.get("content")
        # elif input in "/debug":
        #     chat_console.print(obs)
        #     return obs
        else:
            # obs = deduplicate_log(f"{obs}")
            # text = Text(f"{obs}")
            # text.stylize("dim")
            # chat_console.print(Padding(text, (0, 0, 1, 3)))  # Top, Right, Bottom, Left
            obs_param["content"] = input
            # print("print the alternative observation")
            return input

    def _ask_input(
        self,
        memory: ChatMemory,
        system=None,
        tools=None,
        name=None,
        prompt_ask="🧘 [dim]Enter[/dim] [red]exit[/red][dim] or prompt[/dim]",
        skip_inputs=[],
        ignore_inputs=[""],  # Skip empty input by default
    ) -> None | str:
        while True:
            # Prompt the user for input
            user_input = Prompt.ask(prompt_ask).strip().lower()
            print()

            if user_input in skip_inputs:
                return None

            if user_input in ignore_inputs:
                continue

            match user_input:
                case "exit" | "e":
                    chat_console.print("👋 [blue]Goodbye![/blue]")
                    return None

                case "/debug":
                    chat_console.print(memory.get(system))
                    continue

                case "/debug-tool":
                    if tools or len(tools) > 0:
                        chat_console.print(tools)
                    continue

                case "/pop":
                    msg = memory.pop()
                    chat_console.print(msg)
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
                    return user_input

    # def before_thinking(self, memory: ChatMemory, tools=[]) -> bool:
    #     if not self._before_thinking:
    #         return True
    #     return self._ask_input(memory, tools=tools, skip_inputs=["", "yes", "approve"])

    def next_message(self, memory: ChatMemory, tools=[]):
        if len(memory.get(None)) > 0:
            lastChatMessage: ChatCompletionMessageParam = memory.get(None)[-1]
            result = lastChatMessage.get("content").strip()
            chat_console.print(f"✨ {result} \n", style="bold green")
        return self._ask_input(memory, tools=tools, name="user")
        # if msg:
        # ret = memory.get(None)[-1].get("content")
        # delete the last message from memory -> it will add message in the following input
        # memory.pop()
        # return ret
        # return None

    def error(self, message):
        chat_console.print()
        chat_console.print(f"🐞 {message} \n", style="red")

    def before_action(
        self, permission, func_name, func_args, func_edit=0, functions={}
    ) -> bool:
        # check the agent function
        func = functions[func_name]
        return_type = func.__annotations__.get("return")
        if return_type is not None and issubclass(return_type, IAgent):
            # TODO: add other information
            return True

        tool_info = f"🛠  [yellow]{func_name}[/yellow] - [dim]{func_args}[/dim]"
        if func_name == "code_executor":
            chat_console.print(f"🛠  [yellow]{func_args['language']}[/yellow]")
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
                f"🛠  [yellow]cluster: {func_args['cluster_name']}[/yellow]"
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


def spinner(stop_event: threading.Event) -> None:
    """
    Displays a simple spinner in the terminal until the stop_event is set.

    Parameters:
    stop_event (threading.Event): Event to stop the spinner when the task finishes.
    """
    spinner_chars = ["|", "/", "-", "\\"]
    while not stop_event.is_set():  # Continue spinning until the event is set
        for char in spinner_chars:
            if stop_event.is_set():
                break  # Exit immediately if the stop event is set
            sys.stdout.write(
                f"\r{char} "
            )  # \r moves the cursor to the beginning of the line
            sys.stdout.flush()  # Ensures the spinner character is immediately displayed
            time.sleep(0.1)  # Adjust the speed of the spinner

    # To clear the spinner when done, overwrite the spinner with spaces and move the cursor to the start
    sys.stdout.write("\r    \r")  # Overwrites the spinner with spaces (clear the line)
    sys.stdout.flush()
