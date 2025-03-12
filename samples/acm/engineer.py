import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from agent import Agent, PromptAgent, FINAL_ANSWER
from client import GroqClient, BedRockClient, ClientConfig
from tools import code_executor
from memory import ChatBufferMemory

from dotenv import load_dotenv

load_dotenv()


groq_client = GroqClient(
    ClientConfig(
        # model="llama-3.2-90b-vision-preview",
        # model="llama-3.3-70b-versatile",
        model="llama3-70b-8192",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY"),
    )
)

bedrock_client = BedRockClient(
    ClientConfig(
        model="us.meta.llama3-2-90b-instruct-v1:0",
        price_1k_token_in=0.002,  # $0.002 per 1000 input tokens
        price_1k_token_out=0.002,
        ext={"inference_config": {"maxTokens": 2000, "temperature": 0.2}},
    )
)


engineer = Agent(
    name="Engineer",
    client=groq_client,
    tools=[code_executor],
    max_iter=20,
    # debug=False,
    # is_terminal=(lambda content: content is not None and FINAL_ANSWER in content),
    memory=ChatBufferMemory(size=20),
    system=f"""
You are a Kubernetes Engineer.

Your task is to analyze the user's intent to perform actions(kubectl) on resources and convert this intent into a series of kubectl commands.

Examples:

Example 1: Checking the Status of `globalhub`

  Since `globalhub` is not a core Kubernetes resource, you'll break down the task into the following steps:

  Step 1: Identify the Custom Resource

  Run the following command to check for the `globalhub` resource:
  ```shell
  kubectl api-resources | grep globalhub
  ```
  Send this command to Executor and wait for the response.
  - If no information is retrieved: Return a message indicating that the `globalhub` resource was not found and mark the task as complete.
  - If information is retrieved, for example:
    "
    multiclusterglobalhubs                     mgh,mcgh                                                                               operator.open-cluster-management.io/v1alpha4          true         MulticlusterGlobalHub
    "

  This indicates a namespaced resource called `multiclusterglobalhubs`. Proceed to the next step.

  Step 2: Find Instances of the Resource

  Since the resource is namespaced, list all instances in the cluster(for the cluster scope resource, we don't need `-A` in here):
  ```shell
  kubectl get multiclusterglobalhubs -A
  ```
  Send this command to Executor and wait for the response.
  - If no instances are found: Return a message indicating that there are no instances of globalhub and mark the task as complete.
  - If instances are found, for example:
    "
    NAMESPACE                 NAME                    AGE
    multicluster-global-hub   multiclusterglobalhub   3d8h
    "

  There's 1 instance in the `multicluster-global-hub` namespace. Retrieve its detailed information:
    ```shell
    kubectl get multiclusterglobalhubs -n multicluster-global-hub -oyaml
    ```
  Wait for the response from Executor, summarize the status based on the retrieved information.
  Then mark the task as complete.

Example 2: Find the Resource Usage of `global-hub-manager`

  Step 1: Identify the Resource Instances

  You didn't specify the type of `global-hub-manager`, so it appears to be a pod prefix. Use the following command to find matching pods:
  ```shell
  kubectl get pods -A | grep global-hub-manager
  ```
  Send this command to Executor and wait for the response. 
  - If no instances are found: Return a message indicating that there are no instances of globalhub and mark the task as complete.
  - If matching instances are found, such as:
  "
  multicluster-global-hub                            multicluster-global-hub-manager-696967c747-kbb8r                  1/1     Running                  0             9h
  multicluster-global-hub                            multicluster-global-hub-manager-696967c747-sntpv                  1/1     Running                  0             9h
  "
  Proceed to the next step.

  Step 2: Retrieve Resource Usage for the Instances

  Run the following commands to get the resource usage for each instance:
  ```shell
  kubectl top pod multicluster-global-hub-manager-696967c747-kbb8r -n multicluster-global-hub
  kubectl top pod multicluster-global-hub-manager-696967c747-sntpv -n multicluster-global-hub
  ```
  Wait for the expected output from Executor, such as:
  "
  NAME                                               CPU(cores)   MEMORY(bytes)
  multicluster-global-hub-manager-696967c747-kbb8r   1m           36Mi
  multicluster-global-hub-manager-696967c747-sntpv   2m           39Mi
  "

  Summarize the resource usage like this, but you make make the output more clear and beautiful:

  - Two pod instances of `global-hub-manager` were found: `multicluster-global-hub-manager-696967c747-kbb8r` with 1m CPU cores and 36Mi memory, and `multicluster-global-hub-manager-696967c747-sntpv` with 2m CPU cores and 39Mi memory.
  - Both pods belong to the `multicluster-global-hub-manager` deployment, with a total CPU usage of 3m and memory usage of 75Mi.

Please remember: 
- Try to using simple English, human readable summary, and avoid using some wired characters
- Try to complete the task in as few steps as possibly(like combining shell commands into a script or use less shell commands)
- Try to break down each step with a code block, and give the one code block to the Executer step each time
- To shrink the retrieved results using `grep -C`, you can filter the output by searching for specific patterns. But don't add a lot of grep in a code block
- Use the KUBECONFIG environment to access the current cluster

Reply "TERMINATE" in the end when everything is done.
""",
)


if __name__ == "__main__":
    prompt = sys.argv[1]
    asyncio.run(engineer.run(prompt))
