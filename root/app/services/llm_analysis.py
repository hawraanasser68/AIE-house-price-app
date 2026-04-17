from google import genai
import os
from dotenv import load_dotenv
import requests

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def _analysis_with_gemini(prompt: str) -> str:
    if gemini_client is None:
        raise RuntimeError("GEMINI_API_KEY is missing")

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return (response.text or "").strip()


def _analysis_with_openai(prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing")

    response = requests.post(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "temperature": 0.4,
            "messages": [
                {"role": "system", "content": "You are a helpful real estate expert."},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"].strip()

def generate_analysis(features: dict, prediction: float):

    prompt = f"""
You are a real estate expert advising a homebuyer.

Training dataset summary (Ames Housing):
- Median sale price: $163,000
- Price range: $34,900 – $755,000
- Median living area: 1,464 sq ft
- Median overall quality: 6/10

House features: {features}
Predicted price: ${prediction:,.0f}

Provide a short, user-friendly analysis (2-3 sentences):
1. Why this price makes sense based on the features.
2. Key features driving the price.
3. How this price compares to the dataset median — is it a good deal?
"""

    try:
        return _analysis_with_gemini(prompt)
    except Exception as gemini_error:
        try:
            return _analysis_with_openai(prompt)
        except Exception as openai_error:
            return (
                "Could not generate analysis. "
                f"Gemini error: {str(gemini_error)}. "
                f"OpenAI error: {str(openai_error)}"
            )