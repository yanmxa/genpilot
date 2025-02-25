import os
import dspy

from dotenv import load_dotenv

load_dotenv()

# model="llama-3.2-90b-vision-preview",
# model="llama-3.3-70b-versatile",
lm = dspy.LM(
    model="llama-3.3-70b-versatile",
    api_base="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)
dspy.configure(lm=lm)

import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from tools import code_executor, KubectlExecutor
from dspyagent import Agent
from sample.acmdspy.prompt import PlannerPrompt, EngineerPrompt
from sample.acmdspy.advisor import RetrieveAgent
from sample.acmdspy.engineer import EngineerSignature

class PlannerSignature(dspy.Signature):
    task: str = dspy.InputField()
    answer: str = dspy.OutputField()
    

# def transfer_to_advisor(message: str) -> str:
#     """Transfers commands or tasks that require direct interaction with Kubernetes clusters via kubectl.
#     Ensures that the engineer receives all necessary context to complete each task effectively.
#     """
#     return agents["advisor"]

current_dir = os.path.dirname(os.path.realpath(__file__))

advisor = RetrieveAgent("Advisor", os.path.join(current_dir, "runbooks"))

engineer = Agent("KubeEngineer", EngineerSignature.with_instructions(EngineerPrompt), tools=[
  KubectlExecutor.from_yaml(
      os.path.join(current_dir, "kind-cluster-options.yaml")
  ).kubectl_cmd])


def consult_advisor(message: str) -> Agent:
    """
    This tool let the planner to obtain troubleshooting guidelines for an issue from the advisor.
    It should invoke once for a specific issue or task!
    """
    
    return advisor

def delegate_to_engineer(task: str) -> Agent:
    """
    Transfers commands or tasks that require direct interaction with Kubernetes clusters via kubectl. Include the cluster name in the task, avoiding `kubeconfig` or `context` options, as the cluster name provides this information. Do not use placeholders in commands or scripts.
    """
    
    return engineer
  
planner = Agent("Planner", PlannerSignature.with_instructions(PlannerPrompt), tools=[
  consult_advisor, delegate_to_engineer], root=True)
pred = planner(
    task="Why the status of the managed cluster cluster1 is unknown?"
)
print(pred)
print(dspy.inspect_history(n=1))