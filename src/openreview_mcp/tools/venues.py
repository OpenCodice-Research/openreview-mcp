"""Venue discovery and aggregate statistics."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from ..cache import cached
from ..client import OpenReviewClient
from ..schemas import Venue, VenueStats
from ._helpers import content_value, float_or_none

# Seed of commonly-queried venue groups. OpenReview has thousands of venues;
# this is a starter set. For anything else, users can pass a venue_id directly
# to the other tools — nothing here gates access.
_COMMON_VENUES = [
    ("ICLR.cc", "International Conference on Learning Representations"),
    ("NeurIPS.cc", "Neural Information Processing Systems"),
    ("COLM", "Conference on Language Modeling"),
    ("TMLR", "Transactions on Machine Learning Research"),
    ("aclweb.org/ACL/ARR", "ACL Rolling Review"),
    ("ACM.org/KDD", "KDD"),
]

_YEAR_RE = re.compile(r"/(\d{4})/")


@cached(ttl_seconds=24 * 3600)
def list_venues(
    client: OpenReviewClient,
    year: int | None = None,
    series: str | None = None,
) -> list[dict[str, Any]]:
    """List OpenReview venues.

    Best-effort: OpenReview exposes venues as groups with id patterns like
    ``ICLR.cc/2026/Conference``. We query the venues group directly.
    """
    try:
        venues_group = client.v2.get_group("venues")
        venue_ids: list[str] = list(venues_group.members or [])
    except Exception:
        venue_ids = [f"{s}/{year or 2026}/Conference" for s, _ in _COMMON_VENUES]

    result = []
    for vid in venue_ids:
        m = _YEAR_RE.search(vid)
        venue_year = int(m.group(1)) if m else None
        if year and venue_year != year:
            continue
        if series and series not in vid:
            continue
        result.append(
            Venue(
                id=vid,
                year=venue_year,
                website=f"https://openreview.net/group?id={vid}",
            ).model_dump()
        )
    return result


@cached(ttl_seconds=6 * 3600)
def venue_stats(client: OpenReviewClient, venue_id: str) -> dict[str, Any]:
    """Compute aggregate statistics for a venue."""
    submissions = client.v2.get_all_notes(
        invitation=f"{venue_id}/-/Submission",
        details="replies",
    )
    n_subs = len(submissions)

    rating_hist: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    n_accepted = 0

    for note in submissions:
        for reply in note.details.get("replies", []) if note.details else []:
            inv = reply.get("invitations", []) or []
            inv_str = inv[0] if inv else ""
            content = reply.get("content", {})
            if "Official_Review" in inv_str:
                rating = float_or_none(content_value(content, "rating"))
                if rating is not None:
                    rating_hist[str(int(rating))] += 1
            if "Decision" in inv_str:
                decision = content_value(content, "decision", "")
                if decision:
                    decision_counts[decision] += 1
                    if "accept" in decision.lower():
                        n_accepted += 1

    accept_rate = (n_accepted / n_subs) if n_subs and n_accepted else None
    return VenueStats(
        venue_id=venue_id,
        n_submissions=n_subs,
        n_accepted=n_accepted or None,
        accept_rate=accept_rate,
        rating_histogram=dict(rating_hist),
        decisions=dict(decision_counts),
    ).model_dump()
