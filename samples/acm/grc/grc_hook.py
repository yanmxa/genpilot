from typing import Literal
from dataclasses import dataclass
from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule
from typing import Any
from agents import (
    Usage,
    AgentHooks,
    RunContextWrapper,
    Agent,
    Tool,
)  # Adjust imports as needed


@dataclass
class EvaluationFeedback:
    feedback: str
    score: Literal["pass", "needs_improvement", "fail"]


class GrcAgentHooks(AgentHooks):
    def __init__(self, display_name: str):
        self.event_counter = 0
        self.display_name = display_name
        self.console = Console()

    def _usage_to_str(self, usage: Usage) -> str:
        return f"{usage.requests} requests, {usage.input_tokens} input tokens, {usage.output_tokens} output tokens, {usage.total_tokens} total tokens"

    def _print_event(self, message: str, style: str = "bold white") -> None:
        """Helper function to print formatted event messages."""
        self.console.print(Markdown(message), style=style)

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        self.event_counter += 1
        self.console.print(
            Rule(
                title=f"({self.display_name}) Event {self.event_counter}", style="cyan"
            )
        )
        self._print_event(f"🚀 **`{agent.name}` started**", "bold green")
        import sys

        i = input("🚀 ").strip().lower()
        sys.stdout.write("\033[F")  # Move the cursor up one line
        sys.stdout.write("\033[K")  # Clear the line

    async def on_end(
        self, context: RunContextWrapper, agent: Agent, output: Any
    ) -> None:
        self.event_counter += 1
        if isinstance(output, EvaluationFeedback):
            self._print_event(
                f"🌟 {output.score}",
            )
            self._print_event(
                f"📝 {output.feedback}",
            )
        else:
            self._print_event(
                f"🌟 {output}",
            )

    async def on_handoff(
        self, context: RunContextWrapper, agent: Agent, source: Agent
    ) -> None:
        self.event_counter += 1
        self._print_event(
            f"🔄 **Agent `{source.name}` handed off to `{agent.name}`**", "bold magenta"
        )

    async def on_tool_start(
        self, context: RunContextWrapper, agent: Agent, tool: Tool
    ) -> None:
        self.event_counter += 1
        self._print_event(
            f"🛠 **Agent `{agent.name}` started tool `{tool.name}`**", "bold blue"
        )

    async def on_tool_end(
        self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str
    ) -> None:
        self.event_counter += 1
        self._print_event(
            f"✅ **Agent `{agent.name}` finished tool `{tool.name}`**\n\n**Result:** `{result}` \n",
            "bold green",
        )
