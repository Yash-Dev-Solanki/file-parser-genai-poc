import os
import json
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv()) 
from pydantic import SecretStr
from typing import List
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from langchain_core.prompts import PromptTemplate
from langgraph.types import Command
from langchain.messages import ToolMessage
from file_readers import read_flat_file, read_json_file
from models.graph_state import GraphState
from models.layouts_schema import Layout, LayoutColumn, ColumnMetadata
import sqlite3


MATCHING_PROMPT = """
You are given a data point from a flat file consisting of a header, datarow and a footer. You are also provided with a layout definition in json format. This layout definition contains two keys: 'schema' and 'metadata', both of which are lists of json objects. The schema list contains objects representing the columns in the layout in the sqllite column format, consisiting of (cid, name, type, notnull, is_primary_key, default_value). The metadata list contains objects with details about the column positions, lengths, and validations for their corresponding column names.
Your job as a reasoning AI is to determine if the provided layout correctly matches the data point. Only respond with "MATCH" if the layout matches the data point or "NO MATCH" if it does not.

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



layout_matching_llm_model = ChatOpenAI(temperature=0, model_name="gpt-5.2", reasoning_effort= "high",api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")))
layout_structuring_llm_model = ChatOpenAI(temperature=0, model_name="gpt-5.2", reasoning_effort= "high", api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")))
layout_parsing_master_llm_model = ChatOpenAI(temperature=0, model_name="gpt-4o", api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")))


layout_matching_prompt_template = PromptTemplate.from_template(MATCHING_PROMPT)
layout_structuring_prompt_template = PromptTemplate.from_template(LAYOUT_STRUCTURING_PROMPT)


def get_layout_from_table(table_name: str) -> Layout:
    # Setup connections to the Layouts.db and Metadata.db SQLite databases
    with sqlite3.connect("Layouts.db") as layouts_db_connection, sqlite3.connect("Metadata.db") as metadata_db_connection:
        layouts_cursor = layouts_db_connection.cursor()
        metadata_cursor = metadata_db_connection.cursor()

        # Validate table exists in Layouts.db
        layouts_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
        if layouts_cursor.fetchone() is None:
            available = [r[0] for r in layouts_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            ).fetchall()]
            raise ValueError(f"Layout table '{table_name}' not found in Layouts.db. Available tables: {available}")

        # Validate metadata table exists in Metadata.db
        meta_table = f"{table_name}_column_meta"
        metadata_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (meta_table,))
        if metadata_cursor.fetchone() is None:
            available = [r[0] for r in metadata_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            ).fetchall()]
            raise ValueError(f"Metadata table '{meta_table}' not found in Metadata.db. Available tables: {available}")

        # Phase 1: Fetch the layout schema
        layouts_cursor.execute(f"PRAGMA table_info({table_name});")
        schema: List[LayoutColumn] = []
        for (cid, name, type, notnull, default_value, is_primary_key) in layouts_cursor.fetchall():
            schema.append(LayoutColumn(cid=cid, name=name, type=type, notnull=notnull, default_value=default_value, is_primary_key=is_primary_key))

        # Phase 2: Fetch the metadata for this layout
        metadata_cursor.execute(f"SELECT * FROM {meta_table};")
        metadata: List[ColumnMetadata] = []
        for (column_name, start_pos, length, validations, is_decimal, decimal_pos) in metadata_cursor.fetchall():
            metadata.append(ColumnMetadata(
                column_name=column_name,
                start_pos=start_pos,
                length=length,
                validations=validations,
                is_decimal=is_decimal,
                decimal_pos=decimal_pos
            ))

        return Layout(table_name=table_name, schema=schema, metadata=metadata)


def get_next_layout():
    """
    Generator function to fetch layouts from the Layouts.db SQLite database one at a time.
    """
    with sqlite3.connect("Layouts.db") as layouts_db_connection:
        layouts_cursor = layouts_db_connection.cursor()
        layouts_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        layout_table_names = [table[0] for table in layouts_cursor.fetchall()]

    for layout_table_name in layout_table_names:
        yield get_layout_from_table(layout_table_name)
    

@tool
def insert_layout_into_table(sql_query: str, table_name: str):
    """
    Inserts a new layout schema into the Layouts.db SQLite database.
    """
    pass

@tool
def call_layout_matching_tool(header: str, datarow: str, footer: str, layout: Layout) -> str:
    """
    Invokes the reasoning AI to determine if the provided layout matches the data point.
    """

    response = layout_matching_llm_model.invoke(
        layout_matching_prompt_template.format(
            header= header,
            datarow= datarow,
            footer= footer,
            layout= json.dumps(layout.model_dump(), indent=2)
        )
    )

    return response.text.strip()

@tool
def get_layout(header: str, datarow: str, footer: str, layout: Layout) -> str:
    """
    Fetches the layout table from the database that matches the provided data point using the layout matching model.

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

            if result[0] == "MATCH":
                return (f"Found matching layout table: {layout.table_name}")

        except StopIteration:
            return "No matching layout found."
              


@tool
def structure_layout(file_contents: str, table_name: str) -> str:
    """
    Structures the layout based on the provided file contents.
    
    file_contents(str): The contents of the flat file that needs to be parsed and structured.
    table_name(str): The name of the layout table that matched the file contents, which will be used to fetch the layout structure from the database for structuring the layout.
    """
    try:
        layout = get_layout_from_table(table_name)
    except ValueError as e:
        return str(e)

    response = layout_structuring_llm_model.invoke(
        layout_structuring_prompt_template.format(
            layout_structure= layout.model_dump_json(),
            file_contents= file_contents,
            input_flat_file= read_flat_file("sample_files/positional_parser_agent_sample_input.txt"),
            sample_output_json= read_json_file("sample_files/positional_parser_agent_sample_output.json")
        )
    )

    return response.text.strip()


layout_parser_agent = create_agent(
    system_prompt= LAYOUT_PARSING_PROMPT,
    model= layout_parsing_master_llm_model,
    tools= [get_layout, structure_layout]
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