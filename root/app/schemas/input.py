from pydantic import BaseModel

# Client input (query text)
class QueryInput(BaseModel): 
    query: str