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
from sample.acmdspy.prompt import EngineerPrompt

class EngineerSignature(dspy.Signature):
    task: str = dspy.InputField()
    answer: str = dspy.OutputField()
  
# current_dir = os.path.dirname(os.path.realpath(__file__))
# cluster_executor = KubectlExecutor.from_yaml(
#       os.path.join(current_dir, "kind-cluster-options.yaml")
#   )
  
# engineer = Agent("KubeEngineer", EngineerSignature.with_instructions(EngineerPrompt), tools=[cluster_executor.kubectl_cmd])
# pred = engineer(
#     task="What is the current resource usage of the `multiclusterhub-operator` deployment in the `open-cluster-management` namespace?"
# )
# print(pred)
# print(dspy.inspect_history(n=1))

