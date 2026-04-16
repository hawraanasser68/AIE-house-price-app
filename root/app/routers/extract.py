from fastapi import APIRouter
from app.schemas.input import QueryInput
from app.services.llm_extraction import extract_features

router = APIRouter()


@router.post("/extract")
def extract(data: QueryInput):
    result = extract_features(data.query)
    return result