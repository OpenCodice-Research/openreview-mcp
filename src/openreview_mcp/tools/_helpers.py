"""Helpers shared by tool modules.

OpenReview v2 wraps every content field as ``{"value": ...}``; v1 stores
raw values. We normalize both by unwrapping when needed.
"""

from __future__ import annotations

from typing import Any


def content_value(content: dict[str, Any] | None, key: str, default: Any = None) -> Any:
    """Get a content field, unwrapping v2's ``{value: ...}`` if present."""
    if not content:
        return default
    raw = content.get(key)
    if raw is None:
        return default
    if isinstance(raw, dict) and "value" in raw:
        return raw["value"]
    return raw


def float_or_none(x: Any) -> float | None:
    """Coerce an OpenReview rating field (often ``"8: accept"``) to a float."""
    if x is None:
        return None
    if isinstance(x, int | float):
        return float(x)
    if isinstance(x, str):
        head = x.split(":", 1)[0].strip()
        try:
            return float(head)
        except ValueError:
            return None
    return None


def first_signature(note: Any) -> str:
    """Return the first signature on a note (used as anonymized reviewer id)."""
    sigs = getattr(note, "signatures", None) or []
    return sigs[0] if sigs else "anonymous"


def as_str_list(x: Any) -> list[str]:
    """Normalize a content field that may be a string or list-of-strings."""
    if x is None:
        return []
    if isinstance(x, str):
        return [x] if x else []
    if isinstance(x, list):
        return [str(v) for v in x if v]
    return [str(x)]
