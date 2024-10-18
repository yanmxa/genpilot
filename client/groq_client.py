import os
from groq import Groq

from dotenv import load_dotenv

load_dotenv()


class Client:
    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY"),
        )

    def __call__(self, messages):
        chat_completion = self.client.chat.completions.create(
            messages=messages, model="llama3-70b-8192"
        )
        return chat_completion.choices[0].message.content
