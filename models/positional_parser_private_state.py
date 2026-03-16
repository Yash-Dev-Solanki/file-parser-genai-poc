from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from models.layouts_schema import Layout

class PositionalParserPrivateState(AgentState):
    """State management for the positional parser agent."""
    layout_json: str
    parsed_layout: str

class PositionalParserAgentStateMiddleware(AgentMiddleware):
    """Middleware for managing PositionalParserAgentState."""
    state_schema = PositionalParserPrivateState
    tools = []