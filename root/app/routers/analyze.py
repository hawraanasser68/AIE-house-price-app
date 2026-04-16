from fastapi import APIRouter
from app.schemas.analysis import AnalysisInput
from app.services.llm_analysis import generate_analysis

router = APIRouter()

@router.post("/analyze")
def analyze(data: AnalysisInput):
    analysis = generate_analysis(
        data.features,
        data.prediction
    )
    return {
        "analysis": analysis
    }