"""Unified LLM client — calls Gemini AI.

Callers may override the model per request. The default is the model the
deployed system scores with; auxiliary work that does not need a reasoning
model (generating test fixtures, for example) can name a cheaper one, which
keeps both latency and token spend down without changing how answers are
judged.

Every request is counted so a run's API usage can be reported rather than
estimated — see call_stats().
"""

import json
import threading
import time

import requests

from core.config import (
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_ENDPOINT,
)

_stats_lock = threading.Lock()
_stats = {"calls": 0, "by_model": {}, "seconds": 0.0, "errors": 0}


def call_stats() -> dict:
    """Snapshot of API usage since the process started."""
    with _stats_lock:
        return {
            "calls": _stats["calls"],
            "by_model": dict(_stats["by_model"]),
            "seconds": round(_stats["seconds"], 1),
            "errors": _stats["errors"],
        }


def reset_call_stats():
    with _stats_lock:
        _stats.update({"calls": 0, "by_model": {}, "seconds": 0.0, "errors": 0})


def _endpoint_for(model: str | None) -> str:
    if not model or model == GEMINI_MODEL:
        return GEMINI_ENDPOINT
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={GEMINI_API_KEY}"
    )


def _record(model: str, elapsed: float, error: bool = False):
    with _stats_lock:
        _stats["calls"] += 1
        _stats["seconds"] += elapsed
        _stats["by_model"][model] = _stats["by_model"].get(model, 0) + 1
        if error:
            _stats["errors"] += 1


def _call_gemini(prompt: str, temperature: float = None, max_tokens: int = None,
                 model: str = None) -> str:
    if not GEMINI_API_KEY or not GEMINI_ENDPOINT:
        raise RuntimeError("GEMINI_API_KEY not configured.")

    endpoint = _endpoint_for(model)
    used_model = model or GEMINI_MODEL

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature or LLM_TEMPERATURE,
            "maxOutputTokens": max_tokens or LLM_MAX_TOKENS,
        },
    }
    started = time.time()
    try:
        resp = requests.post(endpoint, json=payload, timeout=90)
    except requests.exceptions.Timeout:
        _record(used_model, time.time() - started, error=True)
        raise RuntimeError("Gemini API request timed out.")
    except requests.exceptions.ConnectionError:
        _record(used_model, time.time() - started, error=True)
        raise RuntimeError("Cannot connect to Gemini API.")

    _record(used_model, time.time() - started, error=resp.status_code != 200)

    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {json.dumps(data)[:300]}")

    return candidates[0]["content"]["parts"][0]["text"]


def call_llm(prompt: str, temperature: float = None, max_tokens: int = None,
             model: str = None) -> str:
    return _call_gemini(prompt, temperature, max_tokens, model)


def call_llm_json(prompt: str, temperature: float = None, model: str = None) -> dict:
    instruction = "\n\nRespond ONLY with valid JSON. No markdown fences, no explanation."
    text = call_llm(prompt + instruction, temperature=temperature, model=model)

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
