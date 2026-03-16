from typing import TypedDict
from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware


class Warning(TypedDict):
    """Structured warning/error information."""
    tool_name: str
    message: str


class GraphState(AgentState):
    """State management for graph agents."""
    file_path: str
    file_content: str
    parsed_layout: str
    warnings: list[Warning]
    thread_id: str



class GraphStateMiddleware(AgentMiddleware):
    """Middleware for managing GraphState."""
    state_schema = GraphState
    tools = []