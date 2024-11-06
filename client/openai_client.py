from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Write a haiku about recursion in programming."},
    ],
)

print(completion.choices[0].message)
