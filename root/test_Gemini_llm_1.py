from app.services.llm_extraction import extract_features

test_input = """
A beautiful 3 bedroom house with a big garage, modern kitchen,
located in a good neighborhood. Built in 2005 with large living area.
"""

result = extract_features(test_input)

print("\n=== LLM OUTPUT ===\n")
print(result)