import os
import json
import asyncio
from uuid import uuid4
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv()) 
from pydantic import SecretStr
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from langchain_community.callbacks import StreamlitCallbackHandler
from models.graph_state import GraphState, GraphStateMiddleware
from file_readers import (
    read_csv_raw, 
    read_csv_tool,
    read_flat_file,
    read_flat_file_tool,
    read_xml_file_raw,
    read_xml_tool
)
from agents.delimiter_parser_agent import call_delimiter_parser_tool
from agents.positional_parser_agent import call_layout_parser_agent_tool
from agents.iso20022_parser_agent import call_iso20022_parser_tool
from models.checkpointer import shared_checkpointer

llm_model = ChatOpenAI(temperature=0, model_name="gpt-5.2", reasoning_effort= "low", api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")))
system_prompt = f"""
You are a file parser agent that helps users generate a json layout file from the input data based on a set of predefined rules.
These rules are as follows:
1. You will be provided the path of a input file. If the file path format is not supported, respond with "Unsupported file format".
2. Read the contents of the input file as raw text using the appropriate tools.
3. Analyze the contents of the file and route the data to the relevant parsing agent. If you're not able to determine the appropriate parsing agent, respond with "Unable to determine parsing agent".
4. On the basis of response from the parsing agent, produce a final json string layout file that adheres to the specified structure and formatting guidelines.
5. In the end, call the CreateJSONOutputFile tool to save the output in a json file.


Supported parsing agents: [
    {{
        "tool_name": "delimiter_parser",
        "file_type": "csv",
        "description": "Parses delimited text files such as CSV files into structured JSON format. Supports a set of common delimiters including commas, tabs, and semicolons."
        "sample_input_file_content": {read_csv_raw("sample_files/delimiter_parser_agent_sample_input.csv")},
    }},
    {{
        "tool_name": "layout_parser",
        "file_type": "txt",
        "description": "Parses positional text files into structured JSON format based on predefined layout structures stored in the database."
        "sample_input_file_content": {(read_flat_file("sample_files/positional_parser_agent_sample_input.txt"))},
    }},
    {{
        "tool_name": "iso20022_parser",
        "file_type": "xml",
        "description": "Parses ISO 20022 XML files into structured JSON format by decoding the XML structure and normalizing the data according to ISO 20022 standards."
        "sample_input_file_content": {read_xml_file_raw("sample_files/iso_parser_agent_sample_input.xml")},
    }}
]"""


@tool(name_or_callable= "CreateJSONOutputFile")
def create_json_output_file(runtime: ToolRuntime[GraphState]) -> None:
    """
    Creates a JSON output file from the parsed layout in the agent state.
    """

    parsed_layout = runtime.state.get("parsed_layout", '')
    if not parsed_layout or parsed_layout.casefold() == 'PARSING FAILED'.casefold():
        with open("output_layout.json", "w", encoding="utf-8") as f:
            json.dump({"error": "Parsing failed"}, f, indent=4)
        
        return
    
    # Strip markdown code fences if the LLM wrapped the JSON
    cleaned = parsed_layout.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        # Remove first line (```json or ```) and last line (```)
        cleaned = "\n".join(lines[1:-1]).strip()

    output_data = json.loads(cleaned)
    with open("output_layout.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent= 4)
    

def build_graph_agent():
    agent_tools = [
        read_csv_tool, 
        read_flat_file_tool,
        read_xml_tool,
        call_delimiter_parser_tool, 
        call_layout_parser_agent_tool,
        call_iso20022_parser_tool,
        create_json_output_file
    ]
     
    graph = create_agent(
        model= llm_model,
        tools = agent_tools,
        middleware= [GraphStateMiddleware()],
        system_prompt= system_prompt,
        checkpointer= shared_checkpointer
    )
    
    return graph


# Streams response from an agent executor call to the StreamlitCallbackHandler
def call_parser_agent(file_path, callback_handler: StreamlitCallbackHandler = None):
    agent = build_graph_agent()
    thread_id = str(uuid4())
    graph_input = {
        "messages": [
            {
                "role": "user",
                "content": f"Parse the input file path {file_path} and generate a json layout file according to the predefined rules."
            }
        ], 
        "file_path": file_path,
        "file_content": "",
        "parsed_layout": [],
        "thread_id": thread_id
    }

    response = agent.invoke(graph_input, {"callbacks": [callback_handler]})
    return response["parsed_layout"]



# Keep for langchain agent testing purpose
async def main():
    test_file_path = "test_samples/positional_layout_test.txt"
    agent = build_graph_agent()
    thread_id = str(uuid4())
    graph_input = {
        "messages": [
            {
                "role": "user",
                "content": f"Parse the input file path {test_file_path} and generate a json layout file according to the predefined rules."
            }
        ], 
        "file_path": test_file_path,
        "file_content": "",
        "parsed_layout": [],
        "thread_id": thread_id
    }

    config = {"configurable": {"thread_id": thread_id}}
    async for event in agent.astream_events(graph_input, config=config):
        event_type = event["event"]
        
        if event_type == "on_tool_start":
            print(f"Calling Tool: {event['name']}")
            print("Tool execution started...")

        elif event_type == "on_tool_end":
            print("Tool execution completed.")


if __name__ == "__main__":
    asyncio.run(main())