"""Simple Groq API wrapper for all LLM calls."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from groq import Groq

import config
from utils.schema_validator import validate_json


_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


def call_llm(system_prompt, user_prompt, temperature=None):
    client = _get_client()
    temp = temperature if temperature is not None else config.LLM_TEMPERATURE

    resp = client.chat.completions.create(
        model=config.MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temp,
    )
    return resp.choices[0].message.content or ""


def call_llm_json(system_prompt, user_prompt, required_keys, temperature=None):
    raw = call_llm(system_prompt, user_prompt, temperature=temperature)
    return validate_json(raw, required_keys)


if __name__ == "__main__":
    result = call_llm("Reply briefly.", "Say hello")
    print(f"Response: {result}")

    data = call_llm_json(
        "Return JSON only.",
        'Return {"city": "Paris", "country": "France"}',
        ["city", "country"],
    )
    print(f"JSON: {data}")

    print("LLM Client: Tests passed")
