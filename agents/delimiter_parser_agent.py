import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv()) 
from pydantic import SecretStr
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command
from langchain.messages import ToolMessage
from file_readers import read_csv_raw, read_json_file
from models.graph_state import GraphState



DELIMITER_PARSER_AGENT_PROMPT = f"""
You are a delimiter parser agent that converts delimited text data into structured JSON format. Follow these rules:
1. Identify the delimiter used in the text data. Valid delimiters are as follows: commas (,), tabs (\t), and semicolons (;).
2. If column headers are present in the first line of the text data, use them as keys for the JSON objects. If headers are absent, generate generic keys such as "column1", "column2", etc.
3. Parse the text data based on the identified delimiter and convert it into a JSON array of objects. Each object should represent a row of data, with keys derived from the header row.
4. In your final response message, provide only the JSON array without any additional text or explanations if parsing was successful or "Parsing failed" if it was not.

Sample input: 
{read_csv_raw("sample_files/delimiter_parser_agent_sample_input.csv")}

Sample output: {read_json_file("sample_files/delimiter_parser_agent_sample_output.json")}
"""

llm_model = ChatOpenAI(temperature=0, model_name="gpt-4o", api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")))
delimiter_parser_agent = create_agent(
    model= llm_model,
    tools = [],
    system_prompt= DELIMITER_PARSER_AGENT_PROMPT
)


@tool
def call_delimiter_parser_tool(runtime: ToolRuntime[GraphState]) -> Command:
    """
    Invokes the delimiter parser agent to parse delimited text data into structured JSON format.
    """

    response = delimiter_parser_agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": f"Parse the following file content:\n{runtime.state.get('file_content', '')}"
            }
        ]
    })

    parsing_result = response["messages"][-1].text

    return Command(update= {
        "messages": [ToolMessage(content = f"Delimiter parser agent response received.", tool_call_id = runtime.tool_call_id)],
        "parsed_layout": parsing_result
    })
    
    
    