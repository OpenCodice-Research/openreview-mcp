"""Diskcache-backed TTL cache for OpenReview API responses.

OpenReview is slow and rate-limited. Most data (submissions, reviews,
decisions) is immutable once a venue closes review, so caching aggressively
is safe. TTLs are tuned per-entity.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

import diskcache

P = ParamSpec("P")
R = TypeVar("R")

_CACHE_DIR = Path(os.environ.get("OPENREVIEW_CACHE_DIR", Path.home() / ".cache" / "openreview-mcp"))
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_cache = diskcache.Cache(str(_CACHE_DIR), size_limit=1 << 30)  # 1 GiB


def _make_key(fn_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """Build a stable cache key from a function name and its arguments."""
    payload = json.dumps(
        {"fn": fn_name, "args": args, "kwargs": kwargs},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def cached(ttl_seconds: int) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator: cache a function's return value on disk for `ttl_seconds`.

    Skipped entirely if `OPENREVIEW_MCP_NO_CACHE=1`.
    """

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        if os.environ.get("OPENREVIEW_MCP_NO_CACHE") == "1":
            return fn

        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = _make_key(fn.__qualname__, args, kwargs)
            hit = _cache.get(key, default=_MISS)
            if hit is not _MISS:
                return hit  # type: ignore[no-any-return]
            result = fn(*args, **kwargs)
            _cache.set(key, result, expire=ttl_seconds)
            return result

        return wrapper

    return decorator


class _Miss:
    pass


_MISS = _Miss()
