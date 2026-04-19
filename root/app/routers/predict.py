from fastapi import APIRouter
from app.schemas.house_features import HouseFeatures
from app.services.validation import validate_features
from app.services.model import predict_price

router = APIRouter()

@router.post("/predict")
def predict(input_data: HouseFeatures):
    features = input_data.model_dump()

    validation_result = validate_features(features)

    if validation_result["status"] == "incomplete":
        return validation_result

    price = predict_price(validation_result["data"])

    return {
        "status": "success",
        "prediction": price
    }    