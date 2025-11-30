import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv()) 
from pydantic import SecretStr
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from models.graph_state import GraphStateMiddleware


llm_model = ChatOpenAI(temperature=0, model_name="gpt-4o", api_key= SecretStr(os.getenv("OPENAI_API_KEY", "")))
system_prompt = """
You are a file parser agent that helps users generate a json layout file from the input data based on a set of predefined rules.
These rules are as follows:
1. Identify the type of data based on the name of the input file. If the file format provided is not supported, respond with an error message.
2. Read the contents of the input file as raw text with the help of appropriate tools.
3. Parse the raw text data into a structured json layout according to the predefined rules for that file type.
4. Produce a final json layout file that adheres to the specified structure and formatting guidelines.

Supported file formats: ['csv']
Tools available and their usage: {}"""

def build_graph_agent():
    graph = create_agent(
        model= llm_model,
        tools = [],
        middleware= [GraphStateMiddleware()],
        system_prompt= system_prompt
    )

    return graph


if __name__ == "__main__":
    agent = build_graph_agent()
    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": "Parse the input file path 'data.txt' and generate a json layout file according to the predefined rules."
            }
        ], 
        "file_path": "data.txt",
        "file_content": ""
    })

    print("Agent Response:", response)