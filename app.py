import streamlit as st
import os
from graph import call_parser_agent
from models.streamlit_models import ParsingRequest
from langchain_community.callbacks import StreamlitCallbackHandler

if __name__ == "__main__":
    st.title("Graph Agent for File Parsing")
    st.write("This agent can parse various file formats and generate a structured JSON layout based on predefined rules.")

    if "parsing_requests" not in st.session_state:
        st.session_state["parsing_requests"] = []

    uploaded_file = st.file_uploader("Upload a file to parse", type=["csv", "txt", "xml"])

    if uploaded_file is not None:
        file_content = uploaded_file.read().decode("utf-8")
        if not file_content.strip() or 'text/' not in uploaded_file.type:
            st.warning("The uploaded file is empty. Please upload a valid file.")

        else:            
            # Temporarily save the uploaded file to the "uploaded_files" directory for processing by the agent
            os.makedirs("uploaded_files", exist_ok=True)
            save_path = os.path.join("uploaded_files", uploaded_file.name)
            with open(save_path, "w", encoding="utf-8", newline= "") as f:
                f.write(file_content)
            
            saved_file_path = f"uploaded_files/{uploaded_file.name}"
            st.session_state["parsing_requests"].append(ParsingRequest(
                file_name= uploaded_file.name,
                file_content= file_content,
                parsed_layout= ''
            ))
            with st.spinner("Parsing file..."):
                st_callback = StreamlitCallbackHandler(st.container())
                parsed_layout = call_parser_agent(saved_file_path, callback_handler= st_callback)
                st.session_state["parsing_requests"][-1].parsed_layout = parsed_layout
            
            st.text_area("File Content", value=file_content, height=300)
            with st.container(border= True, height=400):
                st.subheader("Parsed Layout")
                st.json(parsed_layout)
            
            # Remove the temporarily saved file after processing
            #os.remove(saved_file_path)

    # parsing_requests_tabs = st.tabs(f"{request['file_name']}" for request in st.session_state["parsing_requests"])
    # for request, tab in zip(st.session_state["parsing_requests"], parsing_requests_tabs):
    #     with tab:
    #         st.subheader(f"File: {request['file_name']}")
    #         st.text_area("File Content", value=request["file_content"], height=200)
    #         st.text_area("Parsed Layout", value=request["parsed_layout"], height=400)


        