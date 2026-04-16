from pydantic import BaseModel

class ExtractResponse(BaseModel):
    features: dict
    missing_features: list[str]