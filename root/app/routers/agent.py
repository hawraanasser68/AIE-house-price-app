from fastapi import APIRouter
from app.schemas.input import QueryInput
from app.schemas.chain_response import ChainResponse
from app.services.llm_extraction import extract_features
from app.services.validation import validate_features
from app.services.model import predict_price
from app.services.llm_analysis import generate_analysis

router = APIRouter()


@router.post("/agent/predict-from-query", response_model=ChainResponse)
def predict_from_query(data: QueryInput):
    errors = []

    # Stage 1: LLM feature extraction
    extraction = extract_features(data.query)
    extracted_features = extraction.get("features", {})
    missing_features = extraction.get("missing_features", [])

    # Stage 2: Validate extracted features
    validation = validate_features(extracted_features)

    if validation["status"] == "incomplete":
        return ChainResponse(
            status="incomplete",
            extracted_features=extracted_features,
            missing_features=validation["missing_fields"],
            errors=["Some required features could not be extracted from the query."],
        )

    # Stage 3: ML price prediction
    try:
        prediction = predict_price(validation["data"])
    except Exception as e:
        errors.append(f"Prediction error: {str(e)}")
        return ChainResponse(
            status="error",
            extracted_features=extracted_features,
            missing_features=missing_features,
            errors=errors,
        )

    # Stage 4: LLM analysis
    try:
        analysis = generate_analysis(extracted_features, prediction)
    except Exception as e:
        errors.append(f"Analysis error: {str(e)}")
        analysis = None

    return ChainResponse(
        status="success",
        extracted_features=extracted_features,
        missing_features=missing_features,
        prediction=prediction,
        analysis=analysis,
        errors=errors,
    )
