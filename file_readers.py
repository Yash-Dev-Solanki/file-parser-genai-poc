from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command
from models.graph_state import GraphState

import json

def read_csv_raw(file_path: str) -> str:
    """Reads a CSV file and returns its content as raw text."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


@tool
def read_csv_tool(runtime: ToolRuntime[GraphState]) -> Command:
    """
    Reads a CSV file and returns its content as raw text.
    """
    
    raw_text = read_csv_raw(runtime.state.get("file_path", ""))
    if raw_text is not None:
        return Command(update= {
            "messages": [ToolMessage(content = "Successfully read CSV file.", tool_call_id = runtime.tool_call_id)],
            "file_content": raw_text
        })
    else:
        return Command(update= {
            "messages": [ToolMessage(content = "Failed to read CSV file.", tool_call_id = runtime.tool_call_id)],
        })


def read_json_file(file_path: str) -> dict:
    """Reads a JSON file and returns its content as a dictionary."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
    
    