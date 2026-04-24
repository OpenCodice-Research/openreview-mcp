"""Offline tool tests with the fake OpenReview client.

These exercise the parsing / filtering code paths: v2 content wrapping,
invitation-based routing, pydantic validation of every dict returned.
"""

from __future__ import annotations

from openreview_mcp.tools import profiles, reviews, submissions, venues


def _v2_content(**fields: object) -> dict[str, object]:
    """Wrap each field in v2's ``{"value": ...}`` envelope."""
    return {k: {"value": v} for k, v in fields.items()}


def test_search_submissions_filters_by_query(fake_client, make_note) -> None:
    notes = [
        make_note(
            "p1",
            invitations=["V/-/Submission"],
            content=_v2_content(
                title="On bias in language models",
                authors=["Alice", "Bob"],
                authorids=["~Alice1", "~Bob1"],
                abstract="We study political bias.",
                keywords=["bias", "LLM"],
                pdf="/pdf/p1.pdf",
            ),
        ),
        make_note(
            "p2",
            invitations=["V/-/Submission"],
            content=_v2_content(
                title="Sparse attention",
                authors=["Carol"],
                authorids=["~Carol1"],
                abstract="Efficient transformers.",
                keywords=["attention"],
            ),
        ),
    ]
    client = fake_client(notes)
    hits = submissions.search_submissions(client, venue_id="V", query="bias")
    assert len(hits) == 1
    assert hits[0]["title"] == "On bias in language models"
    assert hits[0]["pdf_url"] == "https://openreview.net/pdf/p1.pdf"


def test_get_reviews_extracts_scores(fake_client, make_note) -> None:
    replies = [
        make_note(
            "r1",
            forum="forum1",
            invitations=["V/Submission1/-/Official_Review"],
            signatures=["~Reviewer_aaa1"],
            content=_v2_content(
                rating="7: good",
                confidence="4",
                summary="They propose X.",
                strengths="Clear writing.",
                weaknesses="Limited experiments.",
            ),
        ),
        make_note(
            "d1",
            forum="forum1",
            invitations=["V/Submission1/-/Decision"],
            content=_v2_content(decision="Accept (poster)", comment="Solid."),
        ),
    ]
    client = fake_client(replies)
    out = reviews.get_reviews(client, submission_id="forum1")
    assert len(out) == 1
    assert out[0]["rating"] == 7.0
    assert out[0]["reviewer_id"] == "~Reviewer_aaa1"


def test_get_decision_found(fake_client, make_note) -> None:
    replies = [
        make_note(
            "d1",
            forum="forum1",
            invitations=["V/Submission1/-/Decision"],
            content=_v2_content(decision="Reject", comment="Weak baselines."),
        ),
    ]
    client = fake_client(replies)
    dec = reviews.get_decision(client, submission_id="forum1")
    assert dec is not None
    assert dec["decision"] == "Reject"


def test_get_meta_review_absent_returns_none(fake_client) -> None:
    client = fake_client([])
    assert reviews.get_meta_review(client, submission_id="forum1") is None


def test_venue_stats_counts(fake_client, make_note) -> None:
    sub = make_note(
        "s1",
        invitations=["V/-/Submission"],
        content=_v2_content(title="t"),
    )
    sub.details = {
        "replies": [
            {
                "invitations": ["V/Submission1/-/Official_Review"],
                "content": _v2_content(rating="8: very good"),
            },
            {
                "invitations": ["V/Submission1/-/Decision"],
                "content": _v2_content(decision="Accept"),
            },
        ]
    }
    client = fake_client([sub])
    stats = venues.venue_stats(client, venue_id="V")
    assert stats["n_submissions"] == 1
    assert stats["n_accepted"] == 1
    assert stats["rating_histogram"] == {"8": 1}
    assert stats["decisions"] == {"Accept": 1}


def test_get_profile(fake_client) -> None:
    client = fake_client([])
    p = profiles.get_profile(client, profile_id_or_email="~Jane_Doe1")
    assert p["id"] == "~Jane_Doe1"
    assert "Jane Doe" in p["names"]
    assert "Example University" in p["affiliations"]
