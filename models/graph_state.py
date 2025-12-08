from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware

class GraphState(AgentState):
    """State management for graph agents."""
    file_path: str
    file_content: str
    parsed_layout: str



class GraphStateMiddleware(AgentMiddleware):
    """Middleware for managing GraphState."""
    state_schema = GraphState
    tools = []