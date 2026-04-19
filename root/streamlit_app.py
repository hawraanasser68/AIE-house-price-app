import streamlit as st
import requests
import os

BASE_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="House Price Predictor", page_icon="🏠", layout="wide")

st.title("🏠 House Price Prediction")
st.caption("Describe a house, complete missing details, then get a price estimate and AI analysis.")

with st.sidebar:
    st.header("How to use")
    st.markdown("1. Describe the house")
    st.markdown("2. Fill missing details")
    st.markdown("3. Click Predict")
    st.divider()

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

if "prediction" not in st.session_state:
    st.session_state.prediction = None

if "analysis" not in st.session_state:
    st.session_state.analysis = None

# ------------------------
# STEP 1: INPUT
# ------------------------
with st.container(border=True):
    st.subheader("Step 1: Describe the house")
    with st.form("extract_form"):
        query = st.text_area(
            "House description",
            placeholder="Example: A house in NAmes, quality 7, 1500 sq ft, 2 garage cars, built in 2005...",
            height=130,
        )
        submit_extract = st.form_submit_button("Extract Features", use_container_width=True)

if submit_extract:
    if not query.strip():
        st.error("Please describe the house you want.")
    else:
        try:
            with st.spinner("Extracting features..."):
                res = requests.post(
                    f"{BASE_URL}/extract",
                    json={"query": query},
                    timeout=25,
                )
        except requests.RequestException:
            st.error("Could not connect to backend. Start FastAPI on port 8000.")
            st.stop()

        if res.status_code != 200:
            st.error("Failed to extract features. Please try again.")
            st.stop()

        data = res.json()

        if "error" in data:
            st.warning("LLM extraction is currently unavailable. Please fill in all house details manually.")
            # Fallback: assume all features are missing
            data = {feature: None for feature in ALL_FEATURES}
            data["missing_features"] = ALL_FEATURES.copy()

        st.session_state.features = data
        st.session_state.missing = [
            k for k in ALL_FEATURES
            if st.session_state.features.get(k) is None
        ]
        st.session_state.filled = {}
        st.session_state.prediction = None
        st.session_state.analysis = None

# ------------------------
# STEP 2: SHOW ONLY MISSING
# ------------------------
if st.session_state.features is not None:
    missing = st.session_state.missing

    extracted_count = len([k for k in ALL_FEATURES if st.session_state.features.get(k) is not None])
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Features", len(ALL_FEATURES))
    c2.metric("Extracted", extracted_count)
    c3.metric("Missing", len(missing))

    with st.expander("View extracted feature data"):
        st.json(st.session_state.features)

    if len(missing) > 0:
        with st.container(border=True):
            st.subheader("Step 2: Fill missing fields")
            st.warning("Please fill the remaining fields before prediction.")

            col_left, col_right = st.columns(2)
            for i, field in enumerate(missing):
                config = FIELD_CONFIG.get(field, {})
                label = field
                if config.get("unit"):
                    label = f"{field} ({config['unit']})"

                help_text = config.get("help", "")
                example = config.get("example")
                if example:
                    help_text = f"{help_text} Example: {example}"

                target_col = col_left if i % 2 == 0 else col_right
                with target_col:
                    if field in OPTIONS:
                        current = st.session_state.filled.get(field, OPTIONS[field][0])
                        if current not in OPTIONS[field]:
                            current = OPTIONS[field][0]
                        st.session_state.filled[field] = st.selectbox(
                            label,
                            OPTIONS[field],
                            index=OPTIONS[field].index(current),
                            help=help_text,
                            key=f"field_{field}",
                        )
                    elif config.get("widget") == "number":
                        min_val = config.get("min", 0)
                        max_val = config.get("max", 100000)
                        step = config.get("step", 1)
                        val_type = config.get("type", "float")
                        current = st.session_state.filled.get(field)
                        if current is None:
                            current = config.get("example", min_val)

                        if val_type == "int":
                            st.session_state.filled[field] = st.number_input(
                                label,
                                min_value=int(min_val),
                                max_value=int(max_val),
                                value=int(float(current)),
                                step=int(step),
                                help=help_text,
                                key=f"field_{field}",
                            )
                        else:
                            st.session_state.filled[field] = st.number_input(
                                label,
                                min_value=float(min_val),
                                max_value=float(max_val),
                                value=float(current),
                                step=float(step),
                                help=help_text,
                                key=f"field_{field}",
                            )
                    else:
                        st.session_state.filled[field] = st.text_input(
                            label,
                            value=st.session_state.filled.get(field, ""),
                            placeholder=example or "",
                            help=help_text,
                            key=f"field_{field}",
                        )
    else:
        st.success("All required features are available. You can run prediction now.")

    # ------------------------
    # STEP 3: PREDICT
    # ------------------------
    st.subheader("Step 3: Predict")

    if st.button("Predict Price", type="primary", use_container_width=True):

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

        
        missing_after = [k for k in ALL_FEATURES if k not in final_features]

        if len(missing_after) > 0:
            st.error(f"Still missing: {missing_after}")
            st.stop()

        # ------------------------
        # CALL BACKEND
        # ------------------------
        try:
            with st.spinner("Running prediction..."):
                res = requests.post(
                    f"{BASE_URL}/predict",
                    json=final_features,
                    timeout=25,
                )
        except requests.RequestException:
            st.error("Could not connect to prediction service.")
            st.stop()

        if res.status_code != 200:
            st.error("Prediction request failed.")
            st.stop()

        result = res.json()

        if result.get("status") == "incomplete":
            st.error(f"Prediction cannot run. Missing fields: {result.get('missing_fields')}")
        else:
            price = result.get("prediction")
            if price is None:
                st.error("Prediction failed (check backend model input).")
            else:
                st.session_state.prediction = price

                # ------------------------
                # ANALYSIS
                # ------------------------
                try:
                    analyze_res = requests.post(
                        f"{BASE_URL}/analyze",
                        json={"features": final_features, "prediction": price},
                        timeout=25,
                    )
                except requests.RequestException:
                    analyze_res = None

                if analyze_res is not None and analyze_res.status_code == 200:
                    analysis_data = analyze_res.json()
                    st.session_state.analysis = analysis_data.get("analysis", "Analysis not available.")
                else:
                    st.session_state.analysis = "Could not generate analysis."

    if st.session_state.prediction is not None:
        st.subheader("💰 Predicted Price")
        st.success(f"Estimated price: ${float(st.session_state.prediction):,.0f}")

    if st.session_state.analysis:
        with st.container(border=True):
            st.subheader("🏡 Analysis")
            st.markdown(st.session_state.analysis.replace("$", r"\$"))