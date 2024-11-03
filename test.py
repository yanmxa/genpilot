from llama_index.core.memory import VectorMemory

# from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


vector_memory = VectorMemory.from_defaults(
    vector_store=None,  # leave as None to use default in-memory vector store
    embed_model=HuggingFaceEmbedding(model_name="BAAI/bge-small-en"),
    retriever_kwargs={"similarity_top_k": 1},
)


from llama_index.core.llms import ChatMessage

msgs = [
    ChatMessage.from_str("Jerry likes juice.", "user"),
    ChatMessage.from_str("Bob likes burgers.", "user"),
    ChatMessage.from_str("Alice likes apples.", "user"),
]

# load into memory
for m in msgs:
    vector_memory.put(m)

# retrieve from memory
msgs = vector_memory.get("How about Bob?")
print(msgs)


msgs = [
    ChatMessage.from_str("Jerry likes burgers.", "user"),
    ChatMessage.from_str("Bob likes apples.", "user"),
    ChatMessage.from_str("Indeed, Bob likes apples.", "assistant"),
    ChatMessage.from_str("Alice likes juice.", "user"),
]
vector_memory.set(msgs)

print("======================================================================")
msgs = vector_memory.get("How about Bob?")
print(msgs)


msgs = [
    ChatMessage.from_str("Jerry likes burgers.", "user"),
    ChatMessage.from_str("Bob likes juice.", "user"),
]
vector_memory.set(msgs)

vector_memory.reset()

print("======================================================================")
msgs = vector_memory.get("How about Bob?")
print(msgs)


from llama_index.core.memory import (
    VectorMemory,
    SimpleComposableMemory,
    ChatMemoryBuffer,
)

chat_memory_buffer = ChatMemoryBuffer.from_defaults()
