import streamlit as st
import requests

st.title("🏠 House Price Prediction")

# ------------------------
# CONFIG
# ------------------------
OPTIONS = {
    "ExterQual": ["Ex", "Gd", "TA", "Fa", "Po"],
    "KitchenQual": ["Ex", "Gd", "TA", "Fa", "Po"],
    "BsmtQual": ["Ex", "Gd", "TA", "Fa", "Po"],
    "MSZoning": ["RL", "RM", "FV", "RH", "C (all)"],
    "Neighborhood": ["NAmes", "CollgCr", "OldTown", "Edwards", "Somerst"]
}

ALL_FEATURES = [
    "OverallQual", "GrLivArea", "GarageCars", "TotalBsmtSF",
    "FullBath", "YearBuilt", "YearRemodAdd",
    "ExterQual", "KitchenQual", "BsmtQual",
    "Neighborhood", "MSZoning"
]

FIELD_CONFIG = {
    "OverallQual": {
        "widget": "number",
        "type": "int",
        "unit": "quality score",
        "min": 1,
        "max": 10,
        "step": 1,
        "help": "Overall house quality from 1 (poor) to 10 (excellent)",
        "example": "7"
    },
    "GrLivArea": {
        "widget": "number",
        "type": "float",
        "unit": "sq ft",
        "min": 100.0,
        "max": 10000.0,
        "step": 10.0,
        "help": "Above-ground living area in square feet",
        "example": "1500"
    },
    "GarageCars": {
        "widget": "number",
        "type": "int",
        "unit": "cars",
        "min": 0,
        "max": 5,
        "step": 1,
        "help": "Number of car spaces in the garage",
        "example": "2"
    },
    "TotalBsmtSF": {
        "widget": "number",
        "type": "float",
        "unit": "sq ft",
        "min": 0.0,
        "max": 5000.0,
        "step": 10.0,
        "help": "Total basement area in square feet",
        "example": "850"
    },
    "FullBath": {
        "widget": "number",
        "type": "int",
        "unit": "bathrooms",
        "min": 0,
        "max": 5,
        "step": 1,
        "help": "Number of full bathrooms",
        "example": "2"
    },
    "YearBuilt": {
        "widget": "number",
        "type": "int",
        "unit": "year",
        "min": 1800,
        "max": 2026,
        "step": 1,
        "help": "Year the house was originally built",
        "example": "2005"
    },
    "YearRemodAdd": {
        "widget": "number",
        "type": "int",
        "unit": "year",
        "min": 1800,
        "max": 2026,
        "step": 1,
        "help": "Year of the last remodel or addition",
        "example": "2018"
    },
    "Neighborhood": {
        "widget": "text",
        "unit": "name",
        "help": "Neighborhood code or name from your dataset",
        "example": "NAmes"
    },
    "MSZoning": {
        "widget": "text",
        "unit": "zone code",
        "help": "Residential zoning category",
        "example": "RL"
    }
}

# ------------------------
# SESSION STATE INIT
# ------------------------
if "features" not in st.session_state:
    st.session_state.features = None

if "missing" not in st.session_state:
    st.session_state.missing = None

if "filled" not in st.session_state:
    st.session_state.filled = {}

# ------------------------
# STEP 1: INPUT
# ------------------------
query = st.text_area("Describe the house")

if st.button("Submit"):
    if not query.strip():
        st.error("Please describe the house you want.")
    else:
        res = requests.post(
            "http://127.0.0.1:8000/extract",
            json={"query": query}
        )

        if res.status_code != 200:
            st.error("Failed to extract features. Please try again.")
            st.stop()

        data = res.json()

        if "error" in data:
            st.warning("Gemini is currently unavailable. Please fill in all house details manually.")
            # Fallback: assume all features are missing
            data = {feature: None for feature in ALL_FEATURES}
            data["missing_features"] = ALL_FEATURES.copy()

        st.session_state.features = data
        st.session_state.missing = [
            k for k in ALL_FEATURES
            if st.session_state.features.get(k) is None
        ]
        st.session_state.filled = {}

# ------------------------
# STEP 2: SHOW ONLY MISSING
# ------------------------
if st.session_state.features is not None:
    st.subheader("Extracted features")
    st.json(st.session_state.features)

    missing = st.session_state.missing

    if len(missing) > 0:

        st.warning("Please fill missing fields:")

        for field in missing:
            config = FIELD_CONFIG.get(field, {})
            label = field
            if config.get("unit"):
                label = f"{field} ({config['unit']})"

            help_text = config.get("help", "")
            example = config.get("example")
            if example:
                help_text = f"{help_text} Example: {example}"

            if field in OPTIONS:
                st.session_state.filled[field] = st.selectbox(
                    label,
                    OPTIONS[field],
                    help=help_text,
                    key=f"field_{field}"
                )
            else:
                input_help = help_text
                if config.get("widget") == "number":
                    input_help = f"Numeric input expected. {input_help}"
                st.session_state.filled[field] = st.text_input(
                    label,
                    placeholder=example or "",
                    help=input_help,
                    key=f"field_{field}"
                )

    # ------------------------
    # STEP 3: PREDICT
    # ------------------------
    if st.button("Predict"):

        final_features = {}

        # extracted
        for k, v in st.session_state.features.items():
            if v is not None:
                final_features[k] = v

        # filled (WITH TYPE FIX AND VALIDATION)
        for k, v in st.session_state.filled.items():

            if v == "":
                continue

            try:
                if k in ["OverallQual", "GarageCars", "FullBath", "YearBuilt", "YearRemodAdd"]:
                    final_features[k] = int(v)
                elif k in ["GrLivArea", "TotalBsmtSF"]:
                    final_features[k] = float(v)
                else:
                    final_features[k] = v
            except ValueError:
                config = FIELD_CONFIG.get(k, {})
                example = config.get("example", "a valid value")
                st.error(f"Invalid input for {k}: '{v}' is not a valid number. Please enter a number, e.g., {example}.")
                st.stop()

        # 🔥 HARD CHECK (no silent failure)
        missing_after = [k for k in ALL_FEATURES if k not in final_features]

        if len(missing_after) > 0:
            st.error(f"Still missing: {missing_after}")
            st.stop()

        # ------------------------
        # CALL BACKEND
        # ------------------------
        res = requests.post(
            "http://127.0.0.1:8000/predict",
            json=final_features
        )

        result = res.json()

        if result.get("status") == "incomplete":
            st.error(f"Prediction cannot run. Missing fields: {result.get('missing_fields')}")
        else:
            price = result.get("prediction")
            if price is None:
                st.error("Prediction failed (check backend model input).")
            else:
                st.success(f"💰 Predicted Price: {price}")

                # ------------------------
                # ANALYSIS
                # ------------------------
                analyze_res = requests.post(
                    "http://127.0.0.1:8000/analyze",
                    json={"features": final_features, "prediction": price}
                )

                if analyze_res.status_code == 200:
                    analysis_data = analyze_res.json()
                    st.subheader("🏡 Analysis")
                    st.write(analysis_data.get("analysis", "Analysis not available."))
                else:
                    st.warning("Could not generate analysis.")