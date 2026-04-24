"""Submission (paper) search and retrieval."""

from __future__ import annotations

from typing import Any

from ..cache import cached
from ..client import OpenReviewClient
from ..schemas import Submission
from ._helpers import content_value


def _note_to_submission(note: Any, venue_id: str | None = None) -> Submission:
    c = note.content
    pdf_path = content_value(c, "pdf")
    pdf_url = f"https://openreview.net{pdf_path}" if pdf_path else None
    forum_id = getattr(note, "forum", None) or note.id
    return Submission(
        id=note.id,
        forum=forum_id,
        venue_id=venue_id,
        title=content_value(c, "title", "") or "",
        authors=content_value(c, "authors", []) or [],
        author_ids=content_value(c, "authorids", []) or [],
        abstract=content_value(c, "abstract"),
        tl_dr=content_value(c, "TL;DR") or content_value(c, "tldr"),
        keywords=content_value(c, "keywords", []) or [],
        pdf_url=pdf_url,
        html_url=f"https://openreview.net/forum?id={forum_id}",
        cdate=getattr(note, "cdate", None),
    )


@cached(ttl_seconds=6 * 3600)
def search_submissions(
    client: OpenReviewClient,
    venue_id: str,
    query: str | None = None,
    author: str | None = None,
    keywords: list[str] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search submissions in a venue.

    Filtering is applied client-side: OpenReview's server-side search is
    limited, so we fetch all submissions for the venue (cached) and filter.
    """
    notes = client.v2.get_all_notes(invitation=f"{venue_id}/-/Submission")

    q = query.lower() if query else None
    kw = [k.lower() for k in (keywords or [])]
    a = author.lower() if author else None

    matches: list[Submission] = []
    for n in notes:
        sub = _note_to_submission(n, venue_id=venue_id)
        if q:
            blob = f"{sub.title} {sub.abstract or ''}".lower()
            if q not in blob:
                continue
        if a and not any(a in name.lower() for name in sub.authors):
            continue
        if kw:
            sub_kws = {k.lower() for k in sub.keywords}
            if not any(k in sub_kws for k in kw):
                continue
        matches.append(sub)
        if len(matches) >= limit:
            break

    return [m.model_dump() for m in matches]


@cached(ttl_seconds=24 * 3600)
def get_submission(client: OpenReviewClient, submission_id: str) -> dict[str, Any]:
    """Fetch a single submission by its forum/note id."""
    note = client.v2.get_note(submission_id)
    return _note_to_submission(note).model_dump()


@cached(ttl_seconds=6 * 3600)
def search_by_author(
    client: OpenReviewClient,
    author_profile_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """All submissions authored by a given OpenReview profile id."""
    notes = client.v2.get_all_notes(
        content={"authorids": author_profile_id},
        limit=limit,
    )
    return [_note_to_submission(n).model_dump() for n in notes[:limit]]
