from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from typing import TypedDict


class LayoutParserPrivateState(TypedDict):
    """Priavte State management for layout parser agents hidden from user."""
    matched_layout: str
    parsing_output: str

class LayoutParserPrivateStateMiddleware(AgentMiddleware):
    """Middleware for managing LaoutParserPrivateState."""
    state_schema = LayoutParserPrivateState
    tools = []