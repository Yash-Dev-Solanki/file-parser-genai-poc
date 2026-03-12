from typing import Any, List
from pydantic import BaseModel


class LayoutColumn(BaseModel):
    cid: int
    name: str
    type: str
    notnull: bool
    pk: bool
    default_value: Any | None = None

class ColumnMetadata(BaseModel):
    column_name: str
    start_pos: int
    length: int
    validations: str
    is_decimal: bool
    decimal_pos: int

class Layout(BaseModel):
    table_name: str
    schema: List[LayoutColumn]
    metadata: List[ColumnMetadata]
