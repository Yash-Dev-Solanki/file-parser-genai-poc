import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from pydantic import SecretStr
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command
from langchain.messages import ToolMessage
from models.graph_state import GraphState
from file_readers import read_xml_file_raw, read_json_file


ISO_PARSING_PROMPT = f"""
You are a banking analyst tasked with decoding ISO 20022 files and normalizing these files to so that they can stored efficiently keeping only relevant information.  Follow these rules:

1. Analyze the provided ISO 20022 XML file content.
2. As a starting step, earch the web for the message type on the basis of the xsd schema provided in xmlns and append. This message type code should only contain the fileds code & name (e.g., pain.001.001.03 - Customer Credit Transfer Initiation).
3. Also make sure to expand on abbreviations utilized in XML tags so that they are in a human readable form. Make use of the web search tool for this.
4. Ignore the citations provided by the web search tool and focus on generating the parsed json output with only the relevant information.
5. Respond with only the parsed json output string without any additional text or formatting. If parsing fails, respond with "Parsing failed".


You are provided with the following sample input and expected output for reference:
Sample Input ISO 20022 XML File Content:
{read_xml_file_raw("sample_files/iso_parser_agent_sample_input.xml")}
Sample Expected JSON Output:
{read_json_file("sample_files/iso_parser_agent_sample_output.json")}
"""

iso_parsing__base_llm_model = ChatOpenAI(temperature=0, model_name="gpt-5.2", api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")), reasoning_effort= "medium", use_responses_api= True)
web_search_tool = {"type": "web_search_preview"}
iso_parsing_llm_with_search = iso_parsing__base_llm_model.bind_tools([web_search_tool])

iso_parser_agent = create_agent(
    model= iso_parsing_llm_with_search,
    tools = [],
    system_prompt= ISO_PARSING_PROMPT
)

@tool
def call_iso20022_parser_tool(runtime: ToolRuntime[GraphState]) -> Command:
    """
    Invokes the ISO 20022 parser agent to parse ISO 20022 XML file content into structured JSON format.
    """

    response = iso_parser_agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": f"Parse the following ISO 20022 XML file content:\n{runtime.state.get('file_content', '')}"
            }
        ]
    })

    parsing_result = response["messages"][-1].text

    return Command(update= {
        "messages": [ToolMessage(content = f"ISO 20022 parser agent response received.", tool_call_id = runtime.tool_call_id)],
        "parsed_layout": parsing_result
    })