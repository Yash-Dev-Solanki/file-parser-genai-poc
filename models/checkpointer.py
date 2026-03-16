# Create a shared checkpointer to enable memory storage and retrieval across agent interrupts.
from langgraph.checkpoint.memory import InMemorySaver

shared_checkpointer = InMemorySaver()