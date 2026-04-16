from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("gemini_api_key"))

def generate_analysis(features: dict, prediction: float):

    prompt = f"""
You are a real estate expert advising a homebuyer.

House features: {features}
Predicted price: ${prediction:,.0f}

Provide a short, user-friendly analysis (2-3 sentences):
1. Why this price makes sense based on the features.
2. Key features driving the price.
3. Is this a good deal for a buyer? (briefly)
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text