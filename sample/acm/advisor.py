import os
import re
import sys
from typing import Dict, List, Optional, Tuple, Union
import warnings
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionAssistantMessageParam,
)

from txtai.embeddings import Embeddings

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from agent import IAgent
from agent.chat import ChatConsole

warnings.filterwarnings("ignore")

current_dir = os.path.dirname(os.path.realpath(__file__))


# customize an agent can search material from the documents
class RetrieveAgent(IAgent):

    def __init__(
        self,
        name: str,
        index_dir: str,
    ):
        self._name = name
        self._console = ChatConsole(name=name)
        self.embeddings = Embeddings(
            path="sentence-transformers/all-MiniLM-L6-v2",
        )
        self.documents = self._get_documents(index_dir)

        # export OMP_NUM_THREADS=1
        self.embeddings.index(self.documents)

    @property
    def name(self):
        return self._name

    async def run(
        self, message: Union[ChatCompletionMessageParam, str]
    ) -> ChatCompletionAssistantMessageParam | None:
        if isinstance(message, str):
            message = ChatCompletionUserMessageParam(content=message, role="user")
        content = message.get("content")
        user_name = message.get("name", "user")
        self._console.delivery(user_name, f"{self._name}", content)

        raw_doc = self._search(content)
        # self._console.delivery(self._name, user_name, raw_doc)
        return ChatCompletionAssistantMessageParam(
            role="assistant",
            content=f"{raw_doc}",
            name=f"{self._name}",
        )

    def _get_documents(self, run_book_dir):
        all_files = list_files(run_book_dir, "md")
        documents = []
        i = 0
        for file in all_files:
            with open(file, "r") as f:
                content = f.read()
                title, desc = extract_title_and_description(content)
                documents.append((i, f"""Title: {title}\n Description: {desc}""", file))
                # documents.append((i, title, file))
                i = i + 1
        return documents

    def _search(self, message):
        results = self.embeddings.search(message, 2)
        target = ""
        score = 0
        for item in results:
            file = self.documents[item[0]][2]
            item_score = item[1]
            if item_score > score:
                score = item_score
                target = file

            import rich

            console = rich.get_console()
            console.print()
            console.print(f"  Retrieve 📚: {item} - {file}", style="cyan")

        raw_content = ""
        with open(target, "r") as f:
            raw_content = f.read()
        # print(raw_content)
        return raw_content


def list_files(path, file_extension):
    return [
        entry.path
        for entry in os.scandir(path)
        if entry.is_file() and entry.name.endswith(f".{file_extension}")
    ]


# install index all the content, we can choose only embedding the title and description
def extract_title_and_description(markdown_content):
    # Extract title (H1 heading)
    title_match = re.search(r"^# (.+)", markdown_content, re.MULTILINE)
    title = title_match.group(1) if title_match else "No title found"

    # Extract description (the content after the "## Description" heading)
    description_match = re.search(
        r"## Description\s*\n([\s\S]*?)(\n##|\Z)", markdown_content, re.MULTILINE
    )
    description = (
        description_match.group(1).strip()
        if description_match
        else "No description found"
    )

    return title, description


# import sys
# import asyncio

# advisor = RetrieveAgent("advisor", os.path.join(current_dir, "runbooks"))


# async def main():
#     prompt = sys.argv[1]

#     result = await advisor.run(prompt)
#     # print(result)


# if __name__ == "__main__":
#     asyncio.run(main())
