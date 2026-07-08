"""Gemini LLM client — handles all API interactions."""

import json
import requests
from core.config import GEMINI_ENDPOINT, GEMINI_API_KEY


def generate(prompt: str, temperature: float = 0.4) -> str:
    """Send prompt to Gemini, return text response."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured. Check your .env file.")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 16384},
    }
    try:
        resp = requests.post(GEMINI_ENDPOINT, json=payload, timeout=90)
    except requests.exceptions.Timeout:
        raise RuntimeError("Gemini API request timed out (90s). Try again.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot connect to Gemini API. Check your internet connection.")

    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates. Response: {json.dumps(data)[:300]}")

    return candidates[0]["content"]["parts"][0]["text"]


def generate_json(prompt: str, temperature: float = 0.2) -> dict:
    """Send prompt, parse response as JSON."""
    full = prompt + "\n\nRespond ONLY with valid JSON. No markdown fences, no explanation."
    text = generate(full, temperature).strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    if text.startswith("json"):
        text = text[4:]

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse Gemini response as JSON.\n"
            f"Error: {e}\n"
            f"Raw response (first 500 chars): {text[:500]}"
        )
