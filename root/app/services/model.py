import pickle
import os
import numpy as np
import pandas as pd

# get absolute path to model.pkl
MODEL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "best_house_price_model.pkl")
)

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)


def predict_price(features: dict):
    """
    features: dictionary coming from validated input
    """

    # 🔥 Convert to DataFrame with column names
    df = pd.DataFrame([features])

    prediction = model.predict(df)[0]

    return float(prediction)