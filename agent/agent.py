from typing import Union, Tuple


class Agent:

    # https://platform.openai.com/docs/guides/chat-completions/overview
    _role: str = "assistant"
    _system: str = "You are an assistant to solve the specific task or issue "

    def __init__(self, client, name, system=""):
        self._name = name
        self.system = system
        self.client = client
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": self.system})

    def __call__(self, message: Union[str, Tuple[str, str]]):
        if message:
            if isinstance(message, str):
                self.messages.append({"role": "user", "content": message})
            elif isinstance(message, tuple) and len(message) == 2:
                name, msg = message
                self.messages.append({"role": "user", "name": name, "content": msg})

        result = self.client(self.messages)
        self.messages.append({"role": self._role, "content": result})
        return result
