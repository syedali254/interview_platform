"""Unified LLM client — routes to Ollama or Gemini based on config."""

import json

import requests

from core.config import (
    LLM_PROVIDER,
    OLLAMA_ENDPOINT,
    OLLAMA_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_MAX_RETRIES,
    GEMINI_API_KEY,
    GEMINI_ENDPOINT,
)


def _call_ollama(prompt: str, temperature: float = None, max_tokens: int = None) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature or LLM_TEMPERATURE,
            "num_predict": max_tokens or LLM_MAX_TOKENS,
        },
    }
    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            resp = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=120)
            if resp.status_code == 200:
                return resp.json()["response"].strip()
        except Exception as e:
            if attempt == LLM_MAX_RETRIES:
                raise RuntimeError(f"Ollama call failed after {LLM_MAX_RETRIES} retries: {e}")
    raise RuntimeError("Ollama call failed — unexpected error.")


def _call_gemini(prompt: str, temperature: float = None, max_tokens: int = None) -> str:
    if not GEMINI_API_KEY or not GEMINI_ENDPOINT:
        raise RuntimeError("GEMINI_API_KEY not configured.")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature or LLM_TEMPERATURE,
            "maxOutputTokens": max_tokens or LLM_MAX_TOKENS,
        },
    }
    try:
        resp = requests.post(GEMINI_ENDPOINT, json=payload, timeout=90)
    except requests.exceptions.Timeout:
        raise RuntimeError("Gemini API request timed out.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot connect to Gemini API.")

    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {json.dumps(data)[:300]}")

    return candidates[0]["content"]["parts"][0]["text"]


def call_llm(prompt: str, temperature: float = None, max_tokens: int = None) -> str:
    if LLM_PROVIDER == "ollama":
        return _call_ollama(prompt, temperature, max_tokens)
    return _call_gemini(prompt, temperature, max_tokens)


def call_llm_json(prompt: str, temperature: float = None) -> dict:
    instruction = "\n\nRespond ONLY with valid JSON. No markdown fences, no explanation."
    text = call_llm(prompt + instruction, temperature=temperature)

    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:]) if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    if text.startswith("json"):
        text = text[4:]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: use json-repair for malformed JSON
    try:
        from json_repair import repair_json
        fixed = repair_json(text)
        return json.loads(fixed)
    except Exception as e2:
        raise RuntimeError(
            f"Failed to parse LLM response as JSON.\n"
            f"Error: {e2}\n"
            f"Raw response (first 500 chars): {text[:500]}"
        )
