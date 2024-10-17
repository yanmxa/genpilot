from typing import Union, Tuple
import os
import sys

from tool import extract_function_info, wikipedia
from client import Client

current_dir = os.path.dirname(os.path.realpath(__file__))

from rich.console import Console
from rich.markdown import Markdown

console = Console()


class Agent:

    # https://platform.openai.com/docs/guides/chat-completions/overview
    _role: str = "assistant"

    def __init__(self, client, name, system, tools=[], debug=False):
        self.client = client

        self.name = name
        self.system = self.load_and_replace_markdown(
            os.path.join(current_dir, "..", "prompt"), name, system, tools
        )
        self.debug = debug
        if debug:
            console.print(Markdown(self.system))
        self.messages = [{"role": "system", "content": self.system}]

    def __call__(self, message: Union[str, Tuple[str, str]]):
        if message:
            if isinstance(message, str):
                self.messages.append({"role": "user", "content": message})
            elif isinstance(message, tuple) and len(message) == 2:
                name, msg = message
                self.messages.append({"role": "user", "name": name, "content": msg})

        result = self.client(self.messages)
        if self.debug:
            console.print_json(result)

        self.messages.append({"role": self._role, "content": result})
        return result

    def load_and_replace_markdown(self, prompt_dir: str, name, system, tools) -> str:
        with open(os.path.join(prompt_dir, "agent.md"), "r") as f:
            agent_guidline = f.read()
        agent_guidline = agent_guidline.replace("{{name}}", name)
        agent_guidline = agent_guidline.replace("{{system}}", system)

        tools_info = ["## Tools available:\n"]
        for tool in tools:
            name, params, doc = extract_function_info(tool)
            tool_md = f"### {name}\n"
            tool_md += f"**Parameters**: {', '.join(params)}\n\n"
            tool_md += f"**Description**:\n\n{doc}\n"
            tools_info.append(tool_md)
        if len(tools) > 0:
            agent_guidline = agent_guidline + "\n".join(tools_info)
        return agent_guidline
