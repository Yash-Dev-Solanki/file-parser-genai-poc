import os
import json
import asyncio
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv()) 
from pydantic import SecretStr
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
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

llm_model = ChatOpenAI(temperature=0, model_name="gpt-4o", api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")))
system_prompt = f"""
You are a file parser agent that helps users generate a json layout file from the input data based on a set of predefined rules.
These rules are as follows:
1. You will be provided the path of a input file. If the file path format is not supported, respond with "Unsupported file format".
2. Read the contents of the input file as raw text using the appropriate tools.
3. Analyze the contents of the file and route the data to the relevant parsing agent. If you're not able to determine the appropriate parsing agent, respond with "Unable to determine parsing agent".
4. On the basis of response from the parsing agent, produce a final json layout file that adheres to the specified structure and formatting guidelines.
5. In the end, create a json output file that contains the generated layout.


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
    
    output_data = json.loads(parsed_layout)
    with open("output_layout.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent= 4)
    

def build_graph_agent():
    graph = create_agent(
        model= llm_model,
        tools = [
            read_csv_tool, 
            read_flat_file_tool,
            read_xml_tool,
            call_delimiter_parser_tool, 
            call_layout_parser_agent_tool,
            call_iso20022_parser_tool,
            create_json_output_file
        ],
        middleware= [GraphStateMiddleware()],
        system_prompt= system_prompt
    )

    return graph


def call_parser_agent(file_path) -> str:
    agent = build_graph_agent()
    graph_input = {
        "messages": [
            {
                "role": "user",
                "content": f"Parse the input file path {file_path} and generate a json layout file according to the predefined rules."
            }
        ], 
        "file_path": file_path,
        "file_content": "",
        "parsed_layout": []
    }

    response = agent.invoke(graph_input)
    return response["parsed_layout"]



# Keep for langchain agent testing purpose
async def main():
    test_file_path = "test_samples/positional_layout_test.txt"
    agent = build_graph_agent()
    graph_input = {
        "messages": [
            {
                "role": "user",
                "content": f"Parse the input file path {test_file_path} and generate a json layout file according to the predefined rules."
            }
        ], 
        "file_path": test_file_path,
        "file_content": "",
        "parsed_layout": []
    }

    async for event in agent.astream_events(graph_input):
        event_type = event["event"]
        
        if event_type == "on_tool_start":
            print(f"Calling Tool: {event['name']}")
            print("Tool execution started...")

        elif event_type == "on_tool_end":
            print("Tool execution completed.")


if __name__ == "__main__":
    asyncio.run(main())