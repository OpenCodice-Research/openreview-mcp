"""User profile retrieval."""

from __future__ import annotations

from typing import Any

from ..cache import cached
from ..client import OpenReviewClient
from ..schemas import Profile


def _extract_names(profile: Any) -> list[str]:
    content = getattr(profile, "content", {}) or {}
    names = content.get("names", []) or []
    out = []
    for n in names:
        if isinstance(n, dict):
            full = n.get("fullname") or " ".join(
                filter(None, [n.get("first"), n.get("middle"), n.get("last")])
            )
            if full:
                out.append(full)
    return out


def _extract_list(profile: Any, key: str) -> list[str]:
    content = getattr(profile, "content", {}) or {}
    raw = content.get(key, []) or []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, str)]
    return []


def _extract_affiliations(profile: Any) -> list[str]:
    content = getattr(profile, "content", {}) or {}
    history = content.get("history", []) or []
    out = []
    for h in history:
        if isinstance(h, dict):
            inst = h.get("institution") or {}
            name = inst.get("name") if isinstance(inst, dict) else None
            if name:
                out.append(name)
    return out


@cached(ttl_seconds=7 * 24 * 3600)
def get_profile(client: OpenReviewClient, profile_id_or_email: str) -> dict[str, Any]:
    """Fetch an OpenReview user profile by id or email."""
    try:
        profile = client.v2.get_profile(profile_id_or_email)
    except Exception:
        profile = client.v1.get_profile(profile_id_or_email)

    content = getattr(profile, "content", {}) or {}
    return Profile(
        id=profile.id,
        names=_extract_names(profile),
        emails=_extract_list(profile, "emails"),
        affiliations=_extract_affiliations(profile),
        homepage=content.get("homepage"),
        gscholar=content.get("gscholar"),
        dblp=content.get("dblp"),
        orcid=content.get("orcid"),
    ).model_dump()
