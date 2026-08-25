"""Reading and formatting the measured results the dissertation reports.

These helpers were duplicated across three chapter modules, which is exactly
how a number ends up formatted one way in Chapter 6 and another in Chapter 7.
They live here so every chapter reads the same data through the same accessor.
"""

from __future__ import annotations


def fmt(value, spec="{:.3f}", missing="not measured") -> str:
    """Format a measurement, or say plainly that it is absent."""
    if value is None:
        return missing
    try:
        return spec.format(value)
    except (TypeError, ValueError):
        return str(value)


def p_value(p) -> str:
    """Report a p-value, collapsing anything below 0.001 to that bound."""
    if p is None:
        return "not measured"
    if p < 0.001:
        return "p < 0.001"
    return f"p = {p:.3f}"


def probe_cases(extra) -> dict:
    """Track B probe cases from the evidence fixture, keyed by opening phrase.

    The full case labels are sentences; keying on the phrase before the first
    comma keeps call sites readable.
    """
    cases = ((extra or {}).get("track_b", {})
             .get("behavioural_probe", {}).get("cases") or [])
    return {c["case"].split(",")[0]: c for c in cases}


def level_mean(stats, level) -> float:
    """Mean judge score for one intended answer-quality level."""
    return ((stats or {}).get("e1_discriminant_validity", {})
            .get("by_level", {}).get(level, {}).get("mean", 0))


def strong_threshold(stats) -> float:
    """The score at or above which the deployed system reports a strong answer."""
    return ((stats or {}).get("e1_discriminant_validity", {})
            .get("calibration", {}).get("thresholds_in_use", {})
            .get("medium_strong", 70))
