import os
import sys
import asyncio

# from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import VectorMemory

import qdrant_client
from qdrant_client.models import Distance, VectorParams
from llama_index.vector_stores.qdrant import QdrantVectorStore

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from client import BedRockClient, GroqClient
from agent import Agent, FINAL_ANSWER
from memory import ChatBufferMemory, ChatVectorMemory

client = qdrant_client.QdrantClient(path="./cache/qdrant_data")
client.create_collection(
    "chef",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

vector_memory = VectorMemory.from_defaults(
    # leave as None to use default in-memory vector store
    vector_store=QdrantVectorStore(
        client=client, collection_name="chef", max_retries=3
    ),
    embed_model=HuggingFaceEmbedding(model_name="BAAI/bge-small-en"),
    retriever_kwargs={"similarity_top_k": 3},
)


# # vector_memory.reset()
# msgs = [
#     ChatMessage.from_str("Jerry likes juice.", "user"),
#     ChatMessage.from_str("Bob likes burgers.", "user"),
#     ChatMessage.from_str("Alice likes apples.", "user"),
# ]
# # load into memory
# for m in msgs:
#     vector_memory.put(m)

chef = Agent(
    client=GroqClient(),
    name="Chef",
    system=f"""You are a chef responsible for identifying each person's likes and dislikes, allowing you to prepare their favorite dishes!
    Prefix the response with '{FINAL_ANSWER}' once the task is complete!""",
    max_iter=10,
    tools=[],
    memory=ChatVectorMemory(
        memory_id="test", buffer_size=10, vector_memory=vector_memory
    ),
)

msg = asyncio.run(chef.run("Which is bob's favorite?"))
