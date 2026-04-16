from pydantic import BaseModel

class AnalysisInput(BaseModel):
    features: dict
    prediction: float