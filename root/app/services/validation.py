REQUIRED_FEATURES = [
    "OverallQual",
    "GrLivArea",
    "GarageCars",
    "TotalBsmtSF",
    "FullBath",
    "YearBuilt",
    "YearRemodAdd",
    "ExterQual",
    "KitchenQual",
    "BsmtQual",
    "Neighborhood",
    "MSZoning"
]


def validate_features(features: dict):
    missing = []

    for feature in REQUIRED_FEATURES:
        if feature not in features or features[feature] is None:
            missing.append(feature)

    if missing:
        return {
            "status": "incomplete",
            "missing_fields": missing
        }

    return {
        "status": "complete",
        "data": features
    }