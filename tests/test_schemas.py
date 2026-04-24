"""Smoke tests: every schema constructs from a minimal payload."""

from __future__ import annotations

from openreview_mcp.schemas import (
    Decision,
    MetaReview,
    Profile,
    Rebuttal,
    Review,
    Submission,
    Venue,
    VenueStats,
)


def test_venue_minimal() -> None:
    v = Venue(id="ICLR.cc/2026/Conference")
    assert v.id == "ICLR.cc/2026/Conference"


def test_venue_stats_defaults() -> None:
    s = VenueStats(venue_id="X", n_submissions=0)
    assert s.rating_histogram == {}
    assert s.decisions == {}


def test_submission_minimal() -> None:
    sub = Submission(id="abc", forum="abc", title="Hello")
    assert sub.authors == []
    assert sub.keywords == []


def test_review_rating_is_float() -> None:
    r = Review(id="r1", forum="f1", reviewer_id="~R1", rating=7.0, confidence=4.0)
    assert isinstance(r.rating, float)


def test_metareview_optional_fields() -> None:
    mr = MetaReview(id="mr", forum="f", ac_id="~AC1")
    assert mr.recommendation is None


def test_rebuttal_reply_to() -> None:
    r = Rebuttal(id="x", forum="f", reply_to="r1", author_id="~A1")
    assert r.reply_to == "r1"


def test_decision_required_fields() -> None:
    d = Decision(id="d", forum="f", decision="Accept (poster)")
    assert "Accept" in d.decision


def test_profile_lists_default_empty() -> None:
    p = Profile(id="~X1")
    assert p.emails == []
    assert p.affiliations == []
