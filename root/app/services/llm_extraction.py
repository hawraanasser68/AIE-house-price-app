import os
import json
from dotenv import load_dotenv
from google import genai
import re

# ======================
# LOAD API KEY
# ======================
load_dotenv()
client = genai.Client(api_key=os.getenv("gemini_api_key"))

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

SYSTEM_PROMPT = """
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

# ======================
# FUNCTION
# ======================
def extract_features(user_text: str):

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=SYSTEM_PROMPT + "\n\nUser: " + user_text
        )

        text = response.text

        # 🔥 REMOVE ```json ... ```
        text = re.sub(r"```json|```", "", text).strip()

        try:
            parsed = json.loads(text)
        except Exception:
            return {
                "error": "Invalid JSON from Gemini",
                "raw_output": response.text
            }

    except Exception as e:
        return {
            "error": f"Gemini API error: {str(e)}",
            "raw_output": ""
        }

    result = {feature: parsed.get(feature) for feature in FEATURES}
    result["missing_features"] = [feature for feature, value in result.items() if value is None]

    return result


if __name__ == "__main__":

    test_input = """
    3 bedroom house with big garage, modern kitchen,
    good neighborhood, built in 2005, large living area
    """

    result = extract_features(test_input)

    print("\n===== RESULT =====\n")
    print(result)    