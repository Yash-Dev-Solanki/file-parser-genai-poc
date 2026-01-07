import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv()) 
from pydantic import SecretStr
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from langchain_core.prompts import PromptTemplate
from langgraph.types import Command
from langchain.messages import ToolMessage
from file_readers import read_flat_file, read_json_file
from models.graph_state import GraphState
from models.layout_parser_private_state import LayoutParserPrivateState
from pymongo import MongoClient



MATCHING_PROMPT = """
You are given a data point from a flat file consisting of a header, datarow and a footer. You are also provided with a parsed layout in JSON format. Your job as a reasoning AI is to determine if the provided layout correctly matches the data point. Only respond with "MATCH" if the layout matches the data point or "NO MATCH" if it does not.

Header: {header}
Datarow: {datarow}
Footer: {footer}
Layout: {layout}
"""


LAYOUT_STRUCTURING_PROMPT = """
You're fulfilling the role of a parsing engine responsible for positional parsing an input data object according to the provided layout structure. You will also be provided a sample input flat file and expected JSON output for reference.

ALSO ENSURE THAT YOUR FINAL RESPONSE CONTAINS ONLY THE JSON OBJECT WITHOUT ANY ADDITIONAL TEXT OR FORMATTING. IF YOU ARE UNABLE TO STRUCTURE THE LAYOUT, RESPOND WITH '[]'.

Layout Structure: {layout_structure}
Input File Content: {file_contents}

Sample Input Flat File: {input_flat_file}
Sample Expected JSON Output: {sample_output_json}"""


LAYOUT_PARSING_PROMPT = """
You are a layout parsing master agent that is responsible for generating accurate JSON layouts for flat files based on provided data samples and guidelines. Follow these rules:
1. Analyze the provided data samples, which include header, datarows, and footer.
2. Follow the specified flow to generate the JSON layout:
   a. Identify the layout corresponding to the data samples provided with the help of the layout matching tool.
   b. If a matching layout is found, use it to structure the data samples into a JSON format using the layout structuring tool.
3. Ensure that the final JSON layout accurately represents the structure of the data samples provided.
4. Append a final message at the end of conversation that contains only the generated JSON layout without any additional text or formatting. If the layout could not be generated, respond with '[]'
"""



layout_matching_llm_model = ChatOpenAI(temperature=0, model_name="gpt-5.2", reasoning_effort= "medium",api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")))
layout_structuring_llm_model = ChatOpenAI(temperature=0, model_name="gpt-5.2", reasoning_effort= "high", api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")))
layout_parsing_master_llm_model = ChatOpenAI(temperature=0, model_name="gpt-4o", api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")))


layout_matching_prompt_template = PromptTemplate.from_template(MATCHING_PROMPT)
layout_structuring_prompt_template = PromptTemplate.from_template(LAYOUT_STRUCTURING_PROMPT)


@tool
def call_layout_matching_tool(header, datarow, footer, layout) -> str:
    """
    Invokes the reasoning AI to determine if the provided layout matches the data point.
    """

    response = layout_matching_llm_model.invoke(
        layout_matching_prompt_template.format(
            header= header,
            datarow= datarow,
            footer= footer,
            layout= layout
        )
    )

    return response.text.strip()

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
client = MongoClient(MONGO_CONNECTION_STRING)
layouts_collection = client[os.getenv("DB_NAME")][os.getenv("LAYOUTS_COLLECTION")]

cursor = layouts_collection.find({})

def get_next_layout():
    for layout in cursor:
        yield layout


@tool
def get_layout(header, datarow, footer, context: LayoutParserPrivateState) -> str:
    """
    Fetches the layout from the database that matches the provided data point using the layout matching model.

    header(str): The header of the flat file
    datarow(str): The first datarow of the flat file
    footer(str): The footer of the flat file
    """
    
    
    layout_generator = get_next_layout()
    while True:
        try:
            layout = next(layout_generator, None)
            if layout is None:
                raise StopIteration

            result = call_layout_matching_tool.invoke({
                "header": header,
                "datarow": datarow,
                "footer": footer,
                "layout": layout
            })

            if result == "MATCH":
                context["matched_layout"] = layout
                return context["matched_layout"]
                
                
        except StopIteration:
            context["matched_layout"] = ""
            return "No matching layout found."
        
            


@tool
def structure_layout(file_contents: str, context: LayoutParserPrivateState) -> str:
    """
    Structures the layout based on the provided file contents.
    
    """

    response = layout_structuring_llm_model.invoke(
        layout_structuring_prompt_template.format(
            layout_structure= context["matched_layout"],
            file_contents= file_contents,
            input_flat_file= read_flat_file("sample_files/positional_parser_agent_sample_input.txt"),
            sample_output_json= read_json_file("sample_files/positional_parser_agent_sample_output.json")
        )
    )

    context["parsing_output"] = response.text.strip()
    return context["parsing_output"]


layout_parser_agent = create_agent(
    system_prompt= LAYOUT_PARSING_PROMPT,
    model= layout_parsing_master_llm_model,
    tools= [get_layout, structure_layout],
    context_schema= LayoutParserPrivateState
)

@tool 
def call_layout_parser_agent_tool(runtime: ToolRuntime[GraphState]) -> Command:
    """
    Invokes the layout parser agent to parse the flat file and generate the layout.
    """

    response = layout_parser_agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": f"Parse the following file content:\n{runtime.state.get('file_content', '')}"
            },
        ],
    }, context= {"matched_layout": "", "parsing_output": ""})

    
    parsing_result = response["messages"][-1].text

    return Command(update= {
        "messages": [ToolMessage(content = f"Layout parser agent response received.", tool_call_id = runtime.tool_call_id)],
        "parsed_layout": parsing_result
    })