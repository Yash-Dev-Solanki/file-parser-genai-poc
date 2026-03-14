from typing import Any, List, Optional
from pydantic import BaseModel


class LayoutColumn(BaseModel):
    cid: int
    name: str
    type: str
    notnull: bool
    is_primary_key: bool
    default_value: Optional[Any] = None


class ColumnMetadata(BaseModel):
    column_name: str
    start_pos: Optional[int] = None
    length: Optional[int] = None
    validations: Optional[str] = None
    is_decimal: bool
    decimal_pos: Optional[int] = None


class Layout(BaseModel):
    table_name: str
    columns: List[LayoutColumn]
    metadata: List[ColumnMetadata]
