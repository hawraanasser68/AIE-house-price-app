import pickle
import os
import numpy as np
import pandas as pd

# get absolute path to model.pkl
MODEL_PATH = "/Users/hawraanasser/Desktop/AIE Assignment 2 House Prices/root/best_house_price_model.pkl"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)


def predict_price(features: dict):
    """
    features: dictionary coming from validated input
    """

    df = pd.DataFrame([features])

    prediction = model.predict(df)[0]

    return float(prediction)