"""Reviews, meta-reviews, rebuttals, and decisions."""

from __future__ import annotations

from typing import Any

from ..cache import cached
from ..client import OpenReviewClient
from ..schemas import Decision, MetaReview, Rebuttal, Review
from ._helpers import as_str_list, content_value, first_signature, float_or_none


def _is_invitation(note: Any, suffix: str) -> bool:
    invitations = getattr(note, "invitations", None) or []
    return any(suffix in inv for inv in invitations)


@cached(ttl_seconds=24 * 3600)
def get_reviews(client: OpenReviewClient, submission_id: str) -> list[dict[str, Any]]:
    """Fetch all official reviews for a submission."""
    replies = client.v2.get_all_notes(forum=submission_id)
    reviews: list[Review] = []
    for n in replies:
        if not _is_invitation(n, "Official_Review"):
            continue
        c = n.content
        reviews.append(
            Review(
                id=n.id,
                forum=n.forum,
                reviewer_id=first_signature(n),
                rating=float_or_none(content_value(c, "rating")),
                confidence=float_or_none(content_value(c, "confidence")),
                soundness=float_or_none(content_value(c, "soundness")),
                presentation=float_or_none(content_value(c, "presentation")),
                contribution=float_or_none(content_value(c, "contribution")),
                summary=content_value(c, "summary"),
                strengths=content_value(c, "strengths"),
                weaknesses=content_value(c, "weaknesses"),
                questions=content_value(c, "questions"),
                limitations=content_value(c, "limitations"),
                ethics_flags=as_str_list(content_value(c, "flag_for_ethics_review")),
                cdate=getattr(n, "cdate", None),
            )
        )
    return [r.model_dump() for r in reviews]


@cached(ttl_seconds=24 * 3600)
def get_meta_review(client: OpenReviewClient, submission_id: str) -> dict[str, Any] | None:
    """Fetch the area-chair meta-review, if present."""
    replies = client.v2.get_all_notes(forum=submission_id)
    for n in replies:
        if not _is_invitation(n, "Meta_Review"):
            continue
        c = n.content
        return MetaReview(
            id=n.id,
            forum=n.forum,
            ac_id=first_signature(n),
            recommendation=content_value(c, "recommendation"),
            metareview=content_value(c, "metareview") or content_value(c, "meta_review"),
            confidence=float_or_none(content_value(c, "confidence")),
            cdate=getattr(n, "cdate", None),
        ).model_dump()
    return None


@cached(ttl_seconds=24 * 3600)
def get_rebuttal(client: OpenReviewClient, submission_id: str) -> list[dict[str, Any]]:
    """Fetch author rebuttals."""
    replies = client.v2.get_all_notes(forum=submission_id)
    out: list[Rebuttal] = []
    for n in replies:
        invitations = getattr(n, "invitations", None) or []
        if not any("Rebuttal" in inv or "Author_Response" in inv for inv in invitations):
            continue
        c = n.content
        out.append(
            Rebuttal(
                id=n.id,
                forum=n.forum,
                reply_to=getattr(n, "replyto", None),
                author_id=first_signature(n),
                text=content_value(c, "comment") or content_value(c, "rebuttal"),
                cdate=getattr(n, "cdate", None),
            )
        )
    return [r.model_dump() for r in out]


@cached(ttl_seconds=24 * 3600)
def get_decision(client: OpenReviewClient, submission_id: str) -> dict[str, Any] | None:
    """Fetch the final accept/reject decision, if posted."""
    replies = client.v2.get_all_notes(forum=submission_id)
    for n in replies:
        if not _is_invitation(n, "Decision"):
            continue
        c = n.content
        return Decision(
            id=n.id,
            forum=n.forum,
            decision=content_value(c, "decision", "") or "",
            comment=content_value(c, "comment"),
            cdate=getattr(n, "cdate", None),
        ).model_dump()
    return None
