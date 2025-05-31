from typing_extensions import Annotated
from typing_extensions import TypedDict


class QueryOutput(TypedDict):
    """Generated SQL query

    Args:
        TypedDict (_type_): _description_
    """

    query: Annotated[str, ..., "Syntatically valid SQL Query"]


class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

class QueryAgent():
    def __init__(self):
        pass
    
    def write_query(self):
        