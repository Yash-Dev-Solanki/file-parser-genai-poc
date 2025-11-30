from langchain.tools import tool
from langgraph.types import Command

@tool(parse_docstring= True)
def read_raw_csv() -> Command:
    """Reads a raw CSV file and returns its content as a string.

    Returns:
        Command: A command object containing the CSV content.
    """
    
    