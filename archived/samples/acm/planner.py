import asyncio
import os
import sys
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from agent import Agent, PromptAgent, FINAL_ANSWER
from client import GroqClient, BedRockClient, ClientConfig
from tools import code_executor
from memory import ChatBufferMemory

from sample.acm.advisor import RetrieveAgent
from sample.acm.engineer import engineer


from dotenv import load_dotenv

load_dotenv()

current_dir = os.path.dirname(os.path.realpath(__file__))

bedrock_client = BedRockClient(
    ClientConfig(
        model="us.meta.llama3-2-90b-instruct-v1:0",
        price_1k_token_in=0.002,  # $0.002 per 1000 input tokens
        price_1k_token_out=0.002,
        ext={"inference_config": {"maxTokens": 2000, "temperature": 0.2}},
    )
)

groq_client = GroqClient(
    ClientConfig(
        model="llama-3.2-90b-vision-preview",
        # model="llama-3.3-70b-versatile",
        # model="llama3-70b-8192",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY"),
    )
)

# llama-3.2-90b-text-preview
groq_client = GroqClient(
    ClientConfig(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY"),
    )
)

import argparse
from agent.agent import IAgent


def parse_args():
    # Create the parser
    parser = argparse.ArgumentParser(description="Read cluster access information.")

    # Add the 'cluster-access' argument
    parser.add_argument(
        "--cluster-access-file",
        type=str,
        required=False,  # Makes the argument required
        help="File to the kubeconfig file for cluster access",
        default=None,
    )

    parser.add_argument(
        "--runbook-dir",
        type=str,
        required=False,  # Makes the argument required
        help="The dir of runbooks for the advisor agent",
        default=None,
    )

    parser.add_argument(
        "--task",
        type=str,
        required=True,  # Makes the argument required
        help="Path to the kubeconfig file for cluster access",
        default=None,
    )

    # Parse the arguments
    args = parser.parse_args()

    cluster_access = "using the `KUBECONFIG` variable to access the cluster"
    if args.cluster_access_file:
        with open(args.cluster_access_file, "r") as f:
            cluster_access = f.read()

    runbook_dir = os.path.join(current_dir, "runbooks")
    if args.runbook_dir:
        runbook_dir = args.runbook_dir

    task = args.task

    return {
        "cluster_access": cluster_access,
        "runbook_dir": runbook_dir,
        "task": task,
    }


agents = {
    "engineer": engineer,
    "advisor": None,
}


def transfer_to_engineer(message: str) -> IAgent:
    """Transfers commands or tasks that require direct interaction with Kubernetes clusters via kubectl.
    Ensures that the engineer receives all necessary context to complete each task effectively.
    """
    return agents["advisor"]


def transfer_to_advisor(message: str) -> Agent:
    """This tool let the planner to obtain troubleshooting guidelines for an issue from the advisor.
    It should invoke once for a specific issue or task!"""
    return agents["advisor"]


if __name__ == "__main__":
    args = parse_args()
    cluster_access = args["cluster_access"]
    task = args["task"]

    advisor = RetrieveAgent("advisor", args["runbook_dir"])
    agents["advisor"] = advisor

    planner = PromptAgent(
        debug=False,
        name="Planner",
        client=bedrock_client,
        tools=[transfer_to_advisor, transfer_to_engineer],
        max_iter=20,
        memory=ChatBufferMemory(size=30),
        system=f"""
You are a troubleshoot Planner for Kubernetes Multi-Cluster Environments(Red Hat Advanced Cluster Management (ACM)

## Objective:

Develop a clear, actionable plan to address issues or tasks in Kubernetes multi-cluster environments managed by Red Hat Advanced Cluster Management (RHACM). Use insights from the advisor to help engineers resolve issues efficiently and effectively.

## Troubleshooting Workflow

### 1. Consult the Advisor:

- Start by consulting the Advisor for troubleshooting guidelines related to the identified issue. The Advisor will provide essential insights and recommended steps tailored to the situation.

- You should only consult the Advisor once for a specific issue or task!

### 2. Draft the Action Plan Based on Advisor Guidance:

- Using the Advisor's guidance, draft a clear action plan outlining potential solutions for the issue.

- Break down each solution into executable steps, specifying the `kubectl` commands needed to interact with the Kubernetes clusters.

- Replacing the resource `namespace`, `name`, or cluster `context` in the advisor's guidance with the values from the specific issue or task the user has presented to you!

### 3. Organize the Steps (Sub-Tasks) for the Engineer:

- Instead of sending individual steps(kubectl command), combine the **related steps into one sub-task** for the engineer. This reduces back-and-forth and enhances efficiency.

- Each sub-task for the engineer should try to equipped with the information: **context**, **intent** and **description**! 

- You should explicit should the steps list of the Sub-Task. For example: 

  Step 1. Check whether the `klusterlet` deployment exists on managed cluster; 
  
  Step 2. If it exist, then check the status for any issues using `kubectl describe ...` or `kubectl get ... -oyaml`
  
  ...

- You should not deliver a repeat sub-task to the engineer, So you need the remember the result of the engineer give it to you!

### 4. Verify After Each Sub-Task Completion:

- **If resolved**: Summarize the workflow and present the outcome.
- **If unresolved**: Review progress, update the checklist as needed, and continue with the next steps.
- **If a new issue arises**: Add potential troubleshooting steps or strategies.

## Access Clusters: Use the following method to specify cluster to access in the plan

{cluster_access}

## Knowledge of the Multi Cluster

Note: This section helps you understand the background when drafting the plan.

1. The cluster that manages other clusters is referred to as the hub cluster. It includes the following customized resources and controllers:

  - `ClusterManager` (Global Resource): This resource configures the hub and is reconciled by the `cluster-manager` controller in the `open-cluster-management` namespace by default. The `cluster-manager` watches the `ClusterManager` resource and installs other components in the `open-cluster-management-hub` namespace, including the `addon-manager`, `placement`, `registration`, and `work` controllers.
  
  - `registration`: This component is responsible for registering managed clusters with the hub. It consists of the `cluster-manager-registration-controller` and the `cluster-manager-registration-webhook`, which watches the `CSR` and `ManagedCluster` resources for the managed cluster.
  
  - `addon-manager`: The `cluster-manager-addon-manager-controller` watches the global `ClusterManagementAddon` resource and the namespaced `ManagedClusterAddon` resource. The `ClusterManagementAddon` represents an addon application for the multi-cluster system. The `ManagedClusterAddon` is associated with a specific managed cluster and exists in the cluster namespace, indicating that the addon has been scheduled to that cluster. A single `ClusterManagementAddon` can correspond to multiple `ManagedClusterAddon` instances.
  
  - Placement: This component schedules workloads to target managed clusters. The `cluster-manager-placement-controller` monitors the namespaced `Placement` resource and produces scheduling decisions in the `PlacementDecision` resource.
  
  - Work: The `cluster-manager-work-webhook` controller/webhook manages the `ManifestWork` resource, which encapsulates Kubernetes resources.
  
2. The clusters managed by the hub are represented by the custom resource `ManagedCluster` (abbreviated as mcl and global in scope) within the hub cluster. You can list the clusters currently managed by the hub using `kubectl get mcl` in the hub cluster. The following components are present in the managed cluster:

  - `klusterlet-agent`: The `klusterlet controller` in the `open-cluster-management` namespace watch the global `Klusterlet Instance(CR)` and installs other controllers such as the `klusterlet-registration-agent` and `klusterlet-work-agent`.
  
  - `klusterlet-registration-agent`: Located in the managed cluster, this agent creates the `CSR` in the hub cluster and monitors/updates the heartbeat(lease) of the `ManagedCluster` in the hub cluster.
  
  - `klusterlet-work-agent`: Also located in the managed cluster, this agent watch the workload(`ManifestWork`) of its namespace in the hub cluster and applies it to the local cluster (the managed cluster). It also updates the `ManifestWork` status in the hub cluster.

**Instructions**

- Once you determine the issue is not exist by the Engineer, Just summarize the result and return. **Don't consult the Advisor more than once** for a specific issue or task!!!

- Each time you recreate a resource, retrieve the original configuration (using `kubectl get ... -o yaml`) before deleting it. Remember the configuration of the resource, based on that create the new one!

- Each time you want to create a resource, you can refer to the exist instance configuration (using `kubectl get ... -o yaml`)!

- Avoid providing checklist/sub-task with placeholders like `kubectl apply -f <file.yaml>`. Always specify the actual value or file name explicitly!

""",
    )
    asyncio.run(planner.run(task))
