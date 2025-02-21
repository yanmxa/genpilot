import os
import dspy
import dsp

from dotenv import load_dotenv

load_dotenv()

# model="llama-3.2-90b-vision-preview",
# model="llama-3.3-70b-versatile",
# model="llama3-70b-8192",
lm = dspy.LM(
    model="llama-3.3-70b-versatile",
    api_base="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)
dspy.configure(lm=lm)

math = dspy.ChainOfThought("question -> answer: float")
result = math(
    question="Two dice are tossed. What is the probability that the sum equals two?"
)
print(result)
