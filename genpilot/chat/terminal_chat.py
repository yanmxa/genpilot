import asyncio
import rich.console
import sys
import rich
import rich.rule
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown
from rich.padding import Padding
import threading
from rich.padding import Padding
from typing import Callable, Any, List, Tuple, Union
import time
from datetime import datetime
import json
from enum import Enum

from litellm import completion
from litellm.utils import (
    ModelResponse,
    CustomStreamWrapper,
    ChatCompletionDeltaToolCall,
)
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion_message_tool_call import Function

from genpilot.abc.agent import ActionPermission, ActionType, Attribute
from genpilot.tools.code_executor import terminal_code_executor_printer
from ..abc.agent import IAgent
from ..abc.chat import IChat
from ..tools.code_executor import code_executor, terminal_code_executor_printer

import logging

# Set logging level to WARNING or higher to suppress INFO level logs
logging.basicConfig(level=logging.WARNING)


class TerminalChat(IChat):
    # Optional OpenAI params: see https://platform.openai.com/docs/api-reference/chat/create
    def __init__(self, avatars={}):
        self.console = rich.get_console()
        self.avatars = {
            "user": "👦",
            "assistant": "🤖",
            "system": "💻",
            "tool": "🛠",
        } | avatars
        self.previous_print = ""

        self.tool_printers = {}
        self.register_tool_printer(code_executor, terminal_code_executor_printer)

    def register_tool_printer(self, func_name: Union[Callable, str], printer: Callable):
        name = func_name
        if isinstance(input, Callable):
            name = func_name.__name__
        self.tool_printers[name] = printer

    def input(
        self, agent: IAgent, message: ChatCompletionMessageParam | str = None
    ) -> bool:
        if not message:
            if not self._ask_input(agent, exit=["exit", "quit"]):
                self.console.print("👋 [blue]Goodbye![/blue] \n")
                agent.attribute.memory.clear()
                return False
            message = agent.attribute.memory.last()
        elif isinstance(message, str):
            message = ChatCompletionUserMessageParam(
                content=message, role="user", name="user"
            )
            agent.attribute.memory.add(message)
            self.forward_print(message=message, to_agent=agent)
        else:
            agent.attribute.memory.add(message)
            self.forward_print(message=message, to_agent=agent)
        return True

    def forward_print(
        self, message: ChatCompletionMessageParam, to_agent: IAgent | str = "user"
    ):
        from_agent_name = message.get("name")
        from_role = message.get("role")
        content = message.get("content")

        to_agent_name = to_agent
        if not isinstance(to_agent_name, str):
            to_agent_name = to_agent.attribute.name

        avatar = self.avatars.get(from_agent_name, self.avatars.get(from_role))
        timestamp = datetime.now().strftime("%H:%M:%S")
        title = f"{avatar} [bold bright_cyan]{from_agent_name}[/bold bright_cyan] ➫ {to_agent_name}: [dim green]({timestamp})[/]"

        self.console.rule(title, align="left", style="dim")
        markdown = Markdown(content)
        self.console.print(Padding(markdown, (1, 0, 1, 3)), end="")
        # print()

    async def reasoning(
        self, agent: IAgent, tool_schemas: List
    ) -> ChatCompletionAssistantMessageParam:
        """
        Facilitates interaction with the LLM model via the aisuite client.

        Args:
            agent (IAgent): The agent to reason with the LLM model.
            client (Client): The aisuite client to interact with the model.
        """
        i = input("🚀 ").strip().lower()
        sys.stdout.write("\033[F")  # Move the cursor up one line
        sys.stdout.write("\033[K")  # Clear the line
        # TODO: can add other action, human in loop
        # self.console.print(tool_schemas)
        if i in ["exit", "e"]:
            return None

        response = None
        avatar = self.avatars.get(agent.attribute.name, self.avatars.get("assistant"))
        try:
            with self.console.status(
                f"{avatar} [cyan]{agent.attribute.name} ...[/]", spinner="aesthetic"
            ):
                response = completion(
                    model=agent.attribute.model_name,
                    messages=agent.attribute.memory.get(),
                    tools=tool_schemas,
                    **agent.attribute.model_config,
                )
        except Exception as e:
            self.console.print(agent.attribute.memory.get())
            print(f"Exception Message: {str(e)}")
            import traceback

            traceback.print_exc()

        completion_message = self.reasoning_print(response, agent)

        message = completion_message.model_dump(mode="json")
        # for 'role:assistant' the following must be satisfied[('messages.2' : property 'refusal' is unsupported
        if message["role"] == "assistant" and "refusal" in message:
            del message["refusal"]
        return message

    # 1. print agent title
    # 2. print agent message content
    #    - print delta with agent title
    #    - print complete with agent title
    # 3. print tool info in tool print
    #    - print agent function without title
    #    - print invoking function with title
    # 4. print tool call in invoking
    def reasoning_print(
        self, response: Union[ModelResponse, CustomStreamWrapper], agent: IAgent
    ) -> ChatCompletionMessage:

        # not print agent tools calls in this function, only print the content
        completion_message = ChatCompletionMessage(role="assistant")
        if isinstance(response, CustomStreamWrapper):
            completion_message_tool_calls: List[ChatCompletionMessageToolCall] = []
            completion_message_content = ""
            print_content = False
            for chunk in response:
                delta = chunk.choices[0].delta
                # print(delta, end="\n")
                # not print tool in here
                if delta.tool_calls:
                    for delta_tool_call in delta.tool_calls:
                        # tool_call is ChatCompletionDeltaToolCall
                        completion_message_tool_calls.append(
                            ChatCompletionMessageToolCall(
                                id=delta_tool_call.id,
                                function=Function(
                                    arguments=delta_tool_call.function.arguments,
                                    name=delta_tool_call.function.name,
                                ),
                                type=delta_tool_call.type,
                            )
                        )
                if delta.content is not None and delta.content != "":
                    # Scenario 1: print delta content
                    if not print_content:
                        self.agent_title_print(agent)
                        print_content = True
                    self.console.print(delta.content, end="")
                    completion_message_content += delta.content
            if len(completion_message_tool_calls) > 0:
                completion_message.tool_calls = completion_message_tool_calls
            if completion_message_content != "":
                self.console.print()  # after print the delta content
                completion_message.content = completion_message_content
        else:
            completion_message = response.choices[0].message
            if completion_message.content:
                # Scenario 2: print complete content
                self.agent_title_print(agent)
                markdown = Markdown(completion_message.content)
                self.console.print(Padding(markdown, (0, 0, 1, 3)))
                # self.console.print(Padding(completion_message.content, (0, 0, 1, 3)))
        return completion_message

    def agent_title_print(self, agent: IAgent):
        if self.previous_print != agent.attribute.name:
            avatar = self.avatars.get(
                agent.attribute.name, self.avatars.get("assistant")
            )
            timestamp = datetime.now().strftime("%H:%M:%S")
            title = f"{avatar} [bright_cyan]{agent.attribute.name}[/bright_cyan] [dim green]({timestamp})[/] :"
            self.console.rule(title, align="left", style="dim")
            print("")
            self.previous_print = agent.attribute.name

    async def acting(
        self, agent: IAgent, action_type: ActionType, func_name, func_args
    ) -> str:
        result = ""
        # print tool info
        if action_type in [ActionType.FUNCTION, ActionType.SERVER]:
            self.tool_print(agent, func_name, func_args)

            # check the permission
            if not self.before_invoking(
                agent,
                func_edit=0,
            ):
                return f"Action({func_name}: {func_args}) are not allowed by the user."

            # invoke function
            with self.console.status(f"", spinner="clock"):
                result = await agent.tool_call(func_name, func_args)

            # print result
            text = Text(f"{result}")
            text.stylize("dim")
            self.console.print(Padding(text, (0, 0, 1, 3)))  # Top, Right, Bottom, Left

        # agent forward
        else:
            result = agent.tool_call(func_name, func_args)

        return result

    # don't need print the agent tool
    def tool_print(self, agent: IAgent, func_name, func_args):
        # Scenario 3: print tool
        self.agent_title_print(agent)
        if func_name in self.tool_printers:
            self.tool_printers[func_name](agent, func_name, func_args)
            print()
            return

        if func_name == "kubectl_cmd":
            block = func_args["command"] + func_args["input"]
            self.console.print(
                f"  🛠  [yellow]cluster: {func_args['cluster_name']}[/yellow]"
            )
            rich.print()
            self.console.print(
                Syntax(
                    block,
                    "shell",
                    theme="monokai",
                    line_numbers=True,
                )
            )
        else:
            self.console.print(
                f"  🛠  [yellow]{func_name}[/yellow] - [dim]{func_args}[/dim]"
            )
        rich.print()

    def before_invoking(self, agent: IAgent, func_edit=0) -> bool:
        # check the agent function
        permission = agent.attribute.permission
        if permission == ActionPermission.NONE:
            return True

        if permission == ActionPermission.AUTO and func_edit == 0:  # enable auto
            return True

        while True:
            proceed = self.console.input(f"  🔛 [dim]Approve ?: [/dim]").strip().upper()
            rich.print()
            if proceed == "Y" or proceed == "yes":
                return True
            elif proceed == "N":
                self.console.print(f"  🚫 Action is canceled by user \n", style="red")
                return False
            else:
                self.console.print(
                    "  🔒 Invalid input! Please enter 'Y' or 'N'.\n", style="yellow"
                )

    def _ask_input(
        self,
        agent: IAgent,
        exit=["exit", "quit"],
        finish=["done"],
        prompt_ask="🧘 ",
    ) -> bool:
        """

        Args:
            agent (IAgent): _description_
            exit (list, optional): _description_. Defaults to [].
            finish (list, optional): _description_. Defaults to [].
            prompt_ask (str, optional): _description_. Defaults to " 🧘 ".

        Returns:
            bool: is stop
        """
        while True:
            user_input = input(prompt_ask).strip().lower()
            # user_input = Prompt.ask(prompt_ask).strip().lower()
            print()

            if user_input in exit:
                return False

            if user_input in finish:
                return True

            match user_input:

                case "":
                    continue

                case "/debug" | "/d":
                    self.console.print(agent.attribute.memory.get())
                    continue

                case "/pop":
                    msg = agent.attribute.memory.last()
                    self.console.print(msg)
                    continue

                case "/add" | "/a":
                    input_content = (
                        user_input.replace("/add", "").replace("/a", "").strip()
                    )
                    if input_content:
                        agent.attribute.memory.add(
                            ChatCompletionUserMessageParam(
                                content=input_content,
                                role="user",
                                name="user",
                            )
                        )
                    continue

                case "/clear":
                    agent.attribute.memory.clear()
                    continue

                case _:
                    agent.attribute.memory.add(
                        ChatCompletionUserMessageParam(
                            content=user_input,
                            role="user",
                            name="user",
                        )
                    )
                    return True
