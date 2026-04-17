import os
import json
from dotenv import load_dotenv
from google import genai
import re
import requests

# ======================
# LOAD API KEY
# ======================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ======================
# SYSTEM PROMPT
# ======================
FEATURES = [
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

SYSTEM_PROMPT_V1 = """
You are a real estate feature extraction system.

Extract structured features from user input.

RULES:
- Only extract explicitly mentioned values
- Do NOT guess missing values
- If unknown → null
- Return ONLY JSON

FEATURES:
- OverallQual
- GrLivArea
- GarageCars
- TotalBsmtSF
- FullBath
- YearBuilt
- YearRemodAdd
- ExterQual
- KitchenQual
- BsmtQual
- Neighborhood
- MSZoning
"""

SYSTEM_PROMPT_V2 = """
You extract house features from user text into strict JSON.

Rules:
- Extract only values explicitly stated by the user.
- If a feature is not explicitly stated, return null.
- Do not invent, infer, or estimate.
- Return JSON only. No markdown, no comments, no extra keys.

Output keys (exactly these):
- OverallQual
- GrLivArea
- GarageCars
- TotalBsmtSF
- FullBath
- YearBuilt
- YearRemodAdd
- ExterQual
- KitchenQual
- BsmtQual
- Neighborhood
- MSZoning

Return this JSON shape:
{
    "OverallQual": null,
    "GrLivArea": null,
    "GarageCars": null,
    "TotalBsmtSF": null,
    "FullBath": null,
    "YearBuilt": null,
    "YearRemodAdd": null,
    "ExterQual": null,
    "KitchenQual": null,
    "BsmtQual": null,
    "Neighborhood": null,
    "MSZoning": null
}
"""


def _get_system_prompt(prompt_version: str) -> str:
        if prompt_version == "v2":
                return SYSTEM_PROMPT_V2
        return SYSTEM_PROMPT_V1


def _parse_json_response(text: str) -> dict:
    cleaned = re.sub(r"```json|```", "", text or "").strip()
    return json.loads(cleaned)


def _extract_with_gemini(user_text: str, system_prompt: str) -> dict:
    if gemini_client is None:
        raise RuntimeError("GEMINI_API_KEY is missing")

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=system_prompt + "\n\nUser: " + user_text,
    )
    return _parse_json_response(response.text)


def _extract_with_openai(user_text: str, system_prompt: str) -> dict:
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
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    text = payload["choices"][0]["message"]["content"]
    return _parse_json_response(text)

# ======================
# FUNCTION
# ======================
def extract_features(user_text: str, prompt_version: str = "v1"):
    parsed = None
    errors = []
    system_prompt = _get_system_prompt(prompt_version)

    try:
        parsed = _extract_with_gemini(user_text, system_prompt)
    except Exception as gemini_error:
        errors.append(f"Gemini failed: {str(gemini_error)}")

        try:
            parsed = _extract_with_openai(user_text, system_prompt)
        except Exception as openai_error:
            errors.append(f"OpenAI failed: {str(openai_error)}")
            return {
                "error": "All extraction providers failed",
                "raw_output": " | ".join(errors),
            }

    result = {feature: parsed.get(feature) for feature in FEATURES}
    result["missing_features"] = [feature for feature in FEATURES if result.get(feature) is None]

    return result


if __name__ == "__main__":

    test_input = """
    3 bedroom house with big garage, modern kitchen,
    good neighborhood, built in 2005, large living area
    """

    result = extract_features(test_input)

    print("\n===== RESULT =====\n")
    print(result)    