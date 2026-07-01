"""Simple JSON validator for LLM responses."""

import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def validate_json(response_str, required_keys):
    text = response_str.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group()
    data = json.loads(text)
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing key: {key}")
    return data


if __name__ == "__main__":
    result = validate_json('{"name": "Alice"}', ["name"])
    print(f"Valid: {result}")

    result = validate_json('Here is the JSON: {"x": 1}', ["x"])
    print(f"Extracted: {result}")

    print("Schema Validator: Tests passed")
