## Integrating GenPilot with MCP Servers

### MCP Configuration Schema

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-brave-api-key-here"
      }
    },
    "youtube": {
      "command": "npx",
      "args": ["-y", "github:anaisbetts/mcp-youtube"],
      "exclude_tools": ["..."] // you can configure to exclude tools from the current mcp server
    },
    "mcp-server-commands": {
      "command": "npx",
      "args": ["mcp-server-commands"],
      "requires_confirmation": [
        "run_command",
        "run_script"
      ],
      "enabled": false     // choose disable or enable it
    },
     "multicluster-mcp-server": {
      "command": "node",
      "args": [".../multicluster-mcp-server/build/index.js"]
    }
  }
}
```

### Constructing an Agent to Connect to the MCP Server - Refactoring

To integrate GenPilot with MCP servers, follow the steps below. This example demonstrates how to create an agent that can connect to the MCP server and execute commands.

```python
import sys
import asyncio
from terminal_chat import TerminalChat  # Make sure to import TerminalChat if required
from agent import Agent  # Ensure the Agent class is imported

async def main():
    if len(sys.argv) < 2:
        print("Usage: python assistant.py <path_to_server_configuration>")
        sys.exit(1)

    terminal = TerminalChat()

    agent = Agent(
        name="Assistant",
        model_config={"name": "groq/llama-3.3-70b-versatile"},
        chat=terminal,
        system="You are an AI assistant",
    )
    try:
        await agent.register_server_tools(sys.argv[1])
        await agent()
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

Execute the script by passing the server configuration file as an argument:

```bash
python samples/mcp/assistant.py ./samples/mcp/assistant-server-config.json
```

### Additional Information

- To build a [TypeScript MCP Server](./server), follow the instructions in the linked folder.
