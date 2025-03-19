from pydantic import BaseModel

class GraphQueryInput(BaseModel):
    query: str
