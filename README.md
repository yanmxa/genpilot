<p align="center">
  <img src="./asset/zen-agent.png" width="260", height="240" />
</p>

---

# GenPilot

**GenPilot** streamlines the creation and management of multi-agent systems powered by Generative AI through an intuitive, user-friendly interface. It allows both developers and end-users to efficiently transform concepts and prototypes into fully realized solutions.

## Installation

Require Python **3.10** or later.

```bash
pip install genpilot
```

## Usage

The client is initialized using `litellm`. Please refer to [the guide for details on different providers](https://docs.litellm.ai/docs/providers).

```python
import genpilot as gp
import asyncio

# 1. User Interface: Also supports Streamlit UI, allowing all agents to share the same chat interface.
terminal = gp.TerminalChat(model_options={"temperature": 0.2, "stream": True})

# 2. Define a Tool to search and summarize information
def search_and_summarize(query):
    """Search for information on the internet and return a summary."""
    return f"Here's the summary for '{query}': [Summarized info]."

# 3. Define an Agent for summarizing search results
info_explorer = gp.Agent(
    name="Information Explorer",
    model_name="groq:llama-3.3-70b-versatile",
    chat=terminal,
    tools=[search_and_summarize],
    system=(
        "Your role is to search the internet and summarize relevant information for a given query. "
        "Use the search tool to find and condense information for the user, ensuring clarity and relevance."
    ),
)

# 4. Run the Agent with a query
response = asyncio.run(info_explorer("What's the latest news about AI advancements?"))
print(response)
```

## Why GenPilot?

- **User-Friendly Interface**: GenPilot offers an intuitive interface for prototyping and quick implementation, whether through a web UI(streamlit, chainlit) or terminal. Get started quickly and seamlessly with minimal effort.

- **MCP Agent**: Leverage the mcpServers provided by the ecosystem to empower agents, enabling them to connect with and interact in a richer, more expansive world.

- **Enhanced Autonomy**: GenPilot can internally register and invoke tools, reducing reliance on external agents and minimizing unnecessary interactions.

- **Governed Actions**

  ![governed action](./asset/action.png)

  GenPilot's actions are governed by three permission levels:

  - **`auto`**: Permission requested only for system/environment-modifying actions.
  - **`always`**: Permission requested for all actions.  
  - **`none`**: No permission requests. 

- **Multi-Agent System**: Seamlessly scale from single-agent tasks to complex multi-agent workflows, inspired by [Routines and Handoffs](https://cookbook.openai.com/examples/orchestrating_agents#executing-routines).

- **Memory** [PROCESSING]: GenPilot enhances accuracy with customizable memory:

  1. `ChatBufferMemory` A short-term memory solution designed to retrieve the most recent message along with the current session context.

  2. `ChatVectorMemory` A long-term memory implementation based on LlamaIndex [vector memory](https://docs.llamaindex.ai/en/stable/examples/agent/memory/vector_memory/).

  > [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/pdf/2310.08560)
  > [CLIN: A CONTINUALLY LEARNING LANGUAGE AGENT FOR RAPID TASK ADAPTATION AND GENERALIZATION](https://arxiv.org/pdf/2310.10134)

  3. `ChatPgMemory` ...

- **RAG Support**: GenPilot integrates a retrieval agent that allows local resource or knowledge integration into the multi-agent system. The default implementation leverages LlamaIndex's [ChatEngine](https://docs.llamaindex.ai/en/stable/examples/chat_engine/chat_engine_best/).

- **Typed Prompt and Auto Optimizer**

  - https://github.com/stanfordnlp/dspy

  - https://github.com/zou-group/textgrad

### Samples

<details>
<summary>This demo provides advice on what to wear when traveling to a city</summary>

[![Watch the demo](https://asciinema.org/a/686709.svg)](https://asciinema.org/a/686709)

</details>

<details>

<summary>This demo uses multi-agent troubleshooting for issues in RedHat ACM</summary>

#### Cluster Unknown

[![Watch the demo](https://asciinema.org/a/687993.svg)](https://asciinema.org/a/687993)

#### Addons Aren't Created

[![Watch the demo](https://asciinema.org/a/689439.svg)](https://asciinema.org/a/689439)

</details>