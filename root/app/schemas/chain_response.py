from pydantic import BaseModel
from typing import Optional, List


class ChainResponse(BaseModel):
    status: str  # "success" | "incomplete" | "error"
    extracted_features: dict
    missing_features: List[str]
    prediction: Optional[float] = None
    analysis: Optional[str] = None
    errors: List[str] = []
