<p align="center">
  <img src="./asset/zen-agent.png" width="260", height="240" />
</p>

---

# ZenAgent

**ZenAgent** empowers developers to create AI assistants, providing the capability to build sophisticated multi-agent systems. Its features include:

- **Boost Autonomy**

  ![alt text](./asset/autonomy.png)
  ZenAgent differ from those in systems like [AutoGen](https://microsoft.github.io/autogen/0.2/). With built-in tools, they operate independently, eliminating the need to rely on other agents for information. This allows them to iterate on a task before delivering results or involving another agent, reducing unnecessary interactions and agents.

- **Tool Integration**

  Unlike [LangChain](https://python.langchain.com/docs/how_to/custom_tools/) or [AutoGen](https://microsoft.github.io/autogen/0.2/docs/tutorial/tool-use/), which require following serval rules to register functions or tools, ZenAgent allows you to simply write a function and add a comment. The agent will automatically use the tool to solve tasks. As shown in the example below, check out sample/agent_tool.py for a quick start.

  ```python
  Agent(
    model_client,
    "Assistant AI", "You are an assistant to solve tasks",
    tools=[wikipedia],
  ).run()
  ```

- **Governed Actions**

  ![governed action](./asset/action.png)
  Actions performed by the ZenAgent are regulated by developers with three permission levels:  
  - **`auto`**: Requests permission only for actions that modify the system or environment[PromptAgent]
  - **`always`**: Requests permission for every action.  
  - **`none`**: Never requests permission.  

- **Multi-Agent System**

  Transitioning the zen-agent into a multi-agent system a straightforward process. The handoff workflow for orchestrating agents draws inspiration from the post [Routines and Handoffs](https://cookbook.openai.com/examples/orchestrating_agents#executing-routines), which details the functionality of the [Swarm](https://github.com/openai/swarm) project. We strive to achieve a harmonious balance, enabling you to create a single agent for specific tasks while effortlessly evolving towards a sophisticated multi-agent framework.

  This demo provides advice on what to wear when traveling to a city: <a href="https://asciinema.org/a/686680">
    <img src="https://asciinema.org/a/686680.svg" alt="asciicast" width="600" height="400">
  </a>

- **Memory** [Planning]  

  Memory capabilities enhance accuracy and optimize the chain of thought by transitioning from stateless to stateful. Unlike RAG (Retrieval-Augmented Generation), which builds knowledge from external sources, our input is based on the agent's own experiences.

  Frameworks like [MemGPT](https://memgpt.ai/) and [LangChain](https://www.langchain.com/) enable agents to memorize experiences. However, Zen-Agent leverages flexible tool integration to treat memory as a tool, allowing for easy decoupling and incorporation, thereby enhancing adaptability.

  > [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/pdf/2310.08560)
  > [CLIN: A CONTINUALLY LEARNING LANGUAGE AGENT FOR RAPID TASK ADAPTATION AND GENERALIZATION](https://arxiv.org/pdf/2310.10134)

