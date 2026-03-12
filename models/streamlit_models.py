from pydantic import BaseModel

class ParsingRequest(BaseModel):
    file_name: str
    file_content: str
    parsed_layout: str