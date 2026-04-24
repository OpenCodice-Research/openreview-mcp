"""Offline tests for the weakness-aggregation tool.

Requires the ``analysis`` extra (sklearn + numpy) installed via dev extras.
"""

from __future__ import annotations

import pytest

sklearn = pytest.importorskip("sklearn")

from openreview_mcp.tools import analysis  # noqa: E402


def _v2_content(**fields: object) -> dict[str, object]:
    return {k: {"value": v} for k, v in fields.items()}


def _submission_with_reviews(
    sub_id: str,
    decision: str,
    weaknesses: list[str],
    make_note,
):
    replies = [
        {
            "invitations": ["V/Submission1/-/Decision"],
            "content": _v2_content(decision=decision),
        }
    ]
    for idx, w in enumerate(weaknesses):
        replies.append(
            {
                "invitations": ["V/Submission1/-/Official_Review"],
                "content": _v2_content(weaknesses=w),
                "signatures": [f"~R_{sub_id}_{idx}"],
            }
        )
    note = make_note(
        sub_id,
        invitations=["V/-/Submission"],
        content=_v2_content(title=f"Paper {sub_id}"),
    )
    note.details = {"replies": replies}
    return note


def test_aggregate_weaknesses_clusters_rejected_reviews(fake_client, make_note) -> None:
    novelty_texts = [
        "The paper lacks novelty and the contribution is incremental at best.",
        "Limited methodological novelty; the work is mostly a reapplication of existing methods.",
        "Novelty is limited since the approach is basically a known technique applied to a new dataset.",
        "The contribution is marginal and not particularly novel compared to prior work.",
    ]
    experiment_texts = [
        "Experiments are insufficient. Missing comparisons against strong baselines.",
        "The evaluation is weak; baselines are missing and ablations are shallow.",
        "Experimental section is thin: no statistical significance, no error bars, no strong baselines.",
        "More experiments with stronger baselines and ablations are needed to support the claims.",
    ]
    # Build 8 rejected submissions, one weakness each, plus one accepted (must be excluded).
    notes = []
    for i, w in enumerate(novelty_texts + experiment_texts):
        notes.append(_submission_with_reviews(f"r{i}", "Reject", [w], make_note))
    notes.append(_submission_with_reviews("a1", "Accept (poster)", ["Strong work."], make_note))

    client = fake_client(notes)
    result = analysis.aggregate_weaknesses(
        client,
        venue_id="V",
        sample_size=50,
        n_clusters=2,
        min_text_length=20,
        seed=0,
    )

    assert result["venue_id"] == "V"
    assert result["n_submissions_sampled"] == 8  # accepted one filtered out
    assert result["n_weakness_texts"] == 8
    assert result["n_clusters"] == 2

    sizes = sorted(c["size"] for c in result["clusters"])
    assert sizes == [4, 4]

    for c in result["clusters"]:
        assert c["top_terms"]
        assert c["exemplars"]
        assert len(c["submission_ids"]) == c["size"]


def test_aggregate_weaknesses_handles_empty_venue(fake_client) -> None:
    result = analysis.aggregate_weaknesses(fake_client([]), venue_id="V")
    assert result["n_weakness_texts"] == 0
    assert result["clusters"] == []
    assert result["n_clusters"] == 0


def test_aggregate_weaknesses_respects_min_text_length(fake_client, make_note) -> None:
    short = _submission_with_reviews("r1", "Reject", ["Too short."], make_note)
    client = fake_client([short])
    result = analysis.aggregate_weaknesses(client, venue_id="V", min_text_length=80)
    assert result["n_weakness_texts"] == 0
