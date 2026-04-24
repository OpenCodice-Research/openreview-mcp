"""FastMCP server: registers all tools against a shared OpenReview client."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import OpenReviewClient
from .tools import profiles, reviews, submissions, venues

mcp = FastMCP("openreview-mcp")
_client = OpenReviewClient()


# ---- Venues ----


@mcp.tool()
def openreview_list_venues(
    year: int | None = None,
    series: str | None = None,
) -> list[dict[str, Any]]:
    """List OpenReview venues, optionally filtered by year (e.g. 2026) or series substring (e.g. "ICLR")."""
    return venues.list_venues(_client, year=year, series=series)


@mcp.tool()
def openreview_venue_stats(venue_id: str) -> dict[str, Any]:
    """Compute submission count, acceptance rate, rating histogram, and decision breakdown for a venue (e.g. "ICLR.cc/2026/Conference")."""
    return venues.venue_stats(_client, venue_id=venue_id)


# ---- Submissions ----


@mcp.tool()
def openreview_search_submissions(
    venue_id: str,
    query: str | None = None,
    author: str | None = None,
    keywords: list[str] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search submissions in a venue by title/abstract query, author name, or keywords."""
    return submissions.search_submissions(
        _client,
        venue_id=venue_id,
        query=query,
        author=author,
        keywords=keywords,
        limit=limit,
    )


@mcp.tool()
def openreview_get_submission(submission_id: str) -> dict[str, Any]:
    """Fetch full metadata for a submission by its forum/note id."""
    return submissions.get_submission(_client, submission_id=submission_id)


@mcp.tool()
def openreview_search_by_author(
    author_profile_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List all submissions authored by a given OpenReview profile id (e.g. "~First_Last1")."""
    return submissions.search_by_author(_client, author_profile_id=author_profile_id, limit=limit)


# ---- Reviews / decisions ----


@mcp.tool()
def openreview_get_reviews(submission_id: str) -> list[dict[str, Any]]:
    """Fetch all official reviews for a submission: ratings, confidence, strengths, weaknesses, questions."""
    return reviews.get_reviews(_client, submission_id=submission_id)


@mcp.tool()
def openreview_get_meta_review(submission_id: str) -> dict[str, Any] | None:
    """Fetch the area-chair meta-review for a submission, if available."""
    return reviews.get_meta_review(_client, submission_id=submission_id)


@mcp.tool()
def openreview_get_rebuttal(submission_id: str) -> list[dict[str, Any]]:
    """Fetch author rebuttals and responses to reviewers."""
    return reviews.get_rebuttal(_client, submission_id=submission_id)


@mcp.tool()
def openreview_get_decision(submission_id: str) -> dict[str, Any] | None:
    """Fetch the final accept/reject decision for a submission, if posted."""
    return reviews.get_decision(_client, submission_id=submission_id)


# ---- Profiles ----


@mcp.tool()
def openreview_get_profile(profile_id_or_email: str) -> dict[str, Any]:
    """Fetch an OpenReview user profile by id (e.g. "~First_Last1") or email."""
    return profiles.get_profile(_client, profile_id_or_email=profile_id_or_email)
