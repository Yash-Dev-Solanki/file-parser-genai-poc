import os
import json
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv()) 
from pydantic import SecretStr
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from models.graph_state import GraphState, GraphStateMiddleware
from file_readers import read_csv_raw, read_csv_tool
from agents.delimiter_parser_agent import call_delimiter_parser_tool

llm_model = ChatOpenAI(temperature=0, model_name="gpt-4o", api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")))
system_prompt = f"""
You are a file parser agent that helps users generate a json layout file from the input data based on a set of predefined rules.
These rules are as follows:
1. Identify the type of data based on the path of the input file. If the file path extension is not supported, respond with "Unsupported file format".
2. Read the contents of the input file as raw text using the appropriate tools.
3. Analyze the contents of the file and route the data to the relevant parsing agent. If you're not able to determine the appropriate parsing agent, respond with "Unable to determine parsing agent".
4. On the basis of response from the parsing agent, produce a final json layout file that adheres to the specified structure and formatting guidelines.
5. In the end, create a json output file that contains the generated layout.



Supported file formats: ['csv',]

Supported parsing agents: [
    {{
        "tool_name": "delimiter_parser",
        "file_type": "csv",
        "description": "Parses delimited text files such as CSV files into structured JSON format. Supports a set of common delimiters including commas, tabs, and semicolons."
        "sample_input_file_content": {read_csv_raw("sample_files/delimiter_parser_agent_sample_input.csv")},
    }},
]"""


@tool
def create_json_output_file(runtime: ToolRuntime[GraphState]) -> None:
    """
    Creates a JSON output file from the parsed layout in the agent state.
    """

    output_data = json.loads(runtime.state.get("parsed_layout", ''))
    with open("output_layout.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent= 4)
    

def build_graph_agent():
    graph = create_agent(
        model= llm_model,
        tools = [read_csv_tool, call_delimiter_parser_tool, create_json_output_file],
        middleware= [GraphStateMiddleware()],
        system_prompt= system_prompt
    )

    return graph


if __name__ == "__main__":
    test_file_path = "test_samples/sample1.csv"
    agent = build_graph_agent()
    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": f"Parse the input file path {test_file_path} and generate a json layout file according to the predefined rules."
            }
        ], 
        "file_path": test_file_path,
        "file_content": "",
        "parsed_layout": []
    })