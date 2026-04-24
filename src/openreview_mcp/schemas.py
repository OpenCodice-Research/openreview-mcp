"""Pydantic schemas for OpenReview entities returned by MCP tools.

Kept intentionally flat and serialization-friendly: every field is either a
primitive, a list of primitives, or a nested model. OpenReview notes are
irregular across venues, so optional fields are the norm.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Venue(BaseModel):
    """A venue group on OpenReview (e.g. ICLR.cc/2026/Conference)."""

    id: str
    name: str | None = None
    year: int | None = None
    website: str | None = None


class VenueStats(BaseModel):
    """Aggregate statistics for a venue."""

    venue_id: str
    n_submissions: int
    n_accepted: int | None = None
    accept_rate: float | None = None
    rating_histogram: dict[str, int] = Field(default_factory=dict)
    decisions: dict[str, int] = Field(default_factory=dict)


class Submission(BaseModel):
    """A paper submitted to an OpenReview venue."""

    id: str
    forum: str
    venue_id: str | None = None
    title: str
    authors: list[str] = Field(default_factory=list)
    author_ids: list[str] = Field(default_factory=list)
    abstract: str | None = None
    tl_dr: str | None = None
    keywords: list[str] = Field(default_factory=list)
    pdf_url: str | None = None
    html_url: str | None = None
    cdate: int | None = None  # creation timestamp (ms since epoch)
    decision: str | None = None


class Review(BaseModel):
    """A single reviewer's review of a submission."""

    id: str
    forum: str
    reviewer_id: str  # anonymized signature
    rating: float | None = None
    confidence: float | None = None
    soundness: float | None = None
    presentation: float | None = None
    contribution: float | None = None
    summary: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    questions: str | None = None
    limitations: str | None = None
    ethics_flag: str | None = None
    cdate: int | None = None


class MetaReview(BaseModel):
    """Area-chair meta-review."""

    id: str
    forum: str
    ac_id: str
    recommendation: str | None = None
    metareview: str | None = None
    confidence: float | None = None
    cdate: int | None = None


class Rebuttal(BaseModel):
    """Author rebuttal to a reviewer."""

    id: str
    forum: str
    reply_to: str | None = None  # review id this rebuts
    author_id: str
    text: str | None = None
    cdate: int | None = None


class Decision(BaseModel):
    """Final accept/reject decision for a submission."""

    id: str
    forum: str
    decision: str
    comment: str | None = None
    cdate: int | None = None


class Profile(BaseModel):
    """OpenReview user profile."""

    id: str
    names: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    homepage: str | None = None
    gscholar: str | None = None
    dblp: str | None = None
    orcid: str | None = None
