import json
from datetime import datetime

from app.services.llm_extraction import FEATURES, extract_features

PROMPT_VERSIONS = ["v1", "v2"]
TEST_CASES = [
    {
        "query": "A 2-story house in NAmes with overall quality 7, 1500 sq ft living area, 2 garage cars, built in 2005 and remodeled in 2018.",
        "expected": {
            "Neighborhood": "NAmes",
            "OverallQual": 7,
            "GrLivArea": 1500.0,
            "GarageCars": 2,
            "YearBuilt": 2005,
            "YearRemodAdd": 2018,
        },
    },
    {
        "query": "Small house in OldTown with 1 full bath, 900 sqft living area, no garage, basement 500 sqft.",
        "expected": {
            "Neighborhood": "OldTown",
            "FullBath": 1,
            "GrLivArea": 900.0,
            "GarageCars": 0,
            "TotalBsmtSF": 500.0,
        },
    },
    {
        "query": "Modern home in CollgCr, excellent kitchen and exterior quality, built in 2016, 3 garage cars, 2200 square feet.",
        "expected": {
            "Neighborhood": "CollgCr",
            "KitchenQual": "Ex",
            "ExterQual": "Ex",
            "YearBuilt": 2016,
            "GarageCars": 3,
            "GrLivArea": 2200.0,
        },
    },
    {
        "query": "RM zoning, Edwards neighborhood, fair basement quality, overall quality 5, year built 1995.",
        "expected": {
            "MSZoning": "RM",
            "Neighborhood": "Edwards",
            "BsmtQual": "Fa",
            "OverallQual": 5,
            "YearBuilt": 1995,
        },
    },
]

LOG_FILE = "prompt_versioning_log.jsonl"


def _values_match(expected, actual) -> bool:
    if isinstance(expected, float):
        return actual is not None and abs(float(actual) - expected) < 1e-6
    return actual == expected


def validate_output(output: dict, expected: dict) -> dict:
    if "error" in output:
        return {
            "is_valid": False,
            "reason": output.get("error", "Unknown error"),
            "extracted_count": 0,
            "missing_count": len(FEATURES),
            "expected_count": len(expected),
            "match_count": 0,
            "recall_on_expected": 0.0,
            "hallucination_count": 0,
        }

    missing_keys = [key for key in FEATURES if key not in output]
    extra_keys = [key for key in output.keys() if key not in FEATURES + ["missing_features"]]

    extracted_count = len([key for key in FEATURES if output.get(key) is not None])
    missing_count = len(output.get("missing_features", []))
    expected_count = len(expected)

    match_count = 0
    for key, expected_value in expected.items():
        if _values_match(expected_value, output.get(key)):
            match_count += 1

    hallucination_count = 0
    for feature in FEATURES:
        if feature not in expected and output.get(feature) is not None:
            hallucination_count += 1

    recall_on_expected = round(match_count / expected_count, 3) if expected_count else 0.0

    if missing_keys:
        return {
            "is_valid": False,
            "reason": f"Missing keys in output: {missing_keys}",
            "extracted_count": extracted_count,
            "missing_count": missing_count,
            "expected_count": expected_count,
            "match_count": match_count,
            "recall_on_expected": recall_on_expected,
            "hallucination_count": hallucination_count,
        }

    if extra_keys:
        return {
            "is_valid": False,
            "reason": f"Unexpected keys in output: {extra_keys}",
            "extracted_count": extracted_count,
            "missing_count": missing_count,
            "expected_count": expected_count,
            "match_count": match_count,
            "recall_on_expected": recall_on_expected,
            "hallucination_count": hallucination_count,
        }

    return {
        "is_valid": True,
        "reason": "Schema and key checks passed",
        "extracted_count": extracted_count,
        "missing_count": missing_count,
        "expected_count": expected_count,
        "match_count": match_count,
        "recall_on_expected": recall_on_expected,
        "hallucination_count": hallucination_count,
    }


def run_experiment() -> None:
    logs = []

    for version in PROMPT_VERSIONS:
        for case in TEST_CASES:
            query = case["query"]
            expected = case["expected"]

            output = extract_features(query, prompt_version=version)
            validation = validate_output(output, expected)

            record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "prompt_version": version,
                "input": query,
                "expected": expected,
                "output": output,
                "validation_result": validation,
            }
            logs.append(record)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for record in logs:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {}
    for version in PROMPT_VERSIONS:
        version_logs = [r for r in logs if r["prompt_version"] == version]
        valid_runs = [r for r in version_logs if r["validation_result"]["is_valid"]]
        extracted_counts = [r["validation_result"]["extracted_count"] for r in version_logs]
        recalls = [r["validation_result"]["recall_on_expected"] for r in version_logs]
        hallucinations = [r["validation_result"]["hallucination_count"] for r in version_logs]

        summary[version] = {
            "total_runs": len(version_logs),
            "valid_runs": len(valid_runs),
            "avg_extracted": round(sum(extracted_counts) / len(extracted_counts), 2),
            "avg_recall_on_expected": round(sum(recalls) / len(recalls), 3),
            "avg_hallucinations": round(sum(hallucinations) / len(hallucinations), 3),
        }

    winner = max(
        summary.items(),
        key=lambda item: (
            item[1]["valid_runs"],
            item[1]["avg_recall_on_expected"],
            -item[1]["avg_hallucinations"],
            item[1]["avg_extracted"],
        ),
    )[0]

    print("Prompt Versioning Results")
    print(json.dumps(summary, indent=2))
    print(f"Selected winner: {winner}")
    print(f"Detailed log written to {LOG_FILE}")


if __name__ == "__main__":
    run_experiment()
