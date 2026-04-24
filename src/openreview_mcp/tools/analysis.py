"""Aggregate analysis across a venue's reviews.

This module's signature tool, ``aggregate_weaknesses``, samples rejected
submissions from a venue, extracts the ``weaknesses`` section from each
official review, and clusters them with TF-IDF + MiniBatchKMeans to surface
recurrent complaint themes.

Clusters are returned as raw top-terms + exemplars, not pre-labelled: the
LLM consuming this MCP is expected to label them itself from the evidence,
which avoids baking a fixed taxonomy into the server.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from ..cache import cached
from ..client import OpenReviewClient
from ..schemas import WeaknessAggregate, WeaknessCluster
from ._helpers import content_value

if TYPE_CHECKING:
    pass


_SKLEARN_ERROR = (
    "openreview_aggregate_weaknesses requires scikit-learn. "
    "Install with `pip install openreview-mcp[analysis]`."
)


def _require_sklearn() -> tuple[Any, Any, Any, Any]:
    """Lazy-import sklearn + numpy. Raise a clear error if the extra is missing."""
    try:
        import numpy as np
        from sklearn.cluster import MiniBatchKMeans
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import euclidean_distances
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(_SKLEARN_ERROR) from e
    return TfidfVectorizer, MiniBatchKMeans, euclidean_distances, np


def _extract_embedded_decision(note: Any) -> str | None:
    """Find the accept/reject label embedded in a submission's replies."""
    details = getattr(note, "details", None) or {}
    replies = details.get("replies") or []
    for reply in replies:
        inv = (reply.get("invitations") or [""])[0]
        if "Decision" in inv:
            decision = content_value(reply.get("content", {}), "decision")
            if isinstance(decision, str):
                return decision
    return None


def _extract_weaknesses(note: Any) -> list[tuple[str, str, str]]:
    """Return ``(submission_id, reviewer_id, weakness_text)`` triples.

    Only non-empty weaknesses from Official_Review replies are returned.
    """
    details = getattr(note, "details", None) or {}
    replies = details.get("replies") or []
    out: list[tuple[str, str, str]] = []
    for reply in replies:
        invs = reply.get("invitations") or []
        if not any("Official_Review" in inv for inv in invs):
            continue
        text = content_value(reply.get("content", {}), "weaknesses")
        if not isinstance(text, str) or not text.strip():
            continue
        signatures = reply.get("signatures") or ["anonymous"]
        out.append((note.id, signatures[0], text.strip()))
    return out


@cached(ttl_seconds=7 * 24 * 3600)
def aggregate_weaknesses(
    client: OpenReviewClient,
    venue_id: str,
    sample_size: int = 50,
    n_clusters: int = 10,
    only_rejected: bool = True,
    min_text_length: int = 80,
    seed: int = 42,
) -> dict[str, Any]:
    """Cluster recurrent weakness themes across a venue's (typically rejected) reviews."""
    TfidfVectorizer, MiniBatchKMeans, euclidean_distances, np = _require_sklearn()

    notes = client.v2.get_all_notes(
        invitation=f"{venue_id}/-/Submission",
        details="replies",
    )

    candidates: list[Any] = []
    for note in notes:
        if only_rejected:
            decision = _extract_embedded_decision(note)
            if not decision or "reject" not in decision.lower():
                continue
        candidates.append(note)

    rng = random.Random(seed)
    sampled = rng.sample(candidates, sample_size) if len(candidates) > sample_size else candidates

    texts: list[str] = []
    meta: list[tuple[str, str]] = []  # (submission_id, reviewer_id)
    for note in sampled:
        for sub_id, reviewer_id, text in _extract_weaknesses(note):
            if len(text) < min_text_length:
                continue
            texts.append(text)
            meta.append((sub_id, reviewer_id))

    if len(texts) < 3:
        return WeaknessAggregate(
            venue_id=venue_id,
            n_submissions_sampled=len(sampled),
            n_weakness_texts=len(texts),
            n_clusters=0,
            clusters=[],
        ).model_dump()

    k = max(2, min(n_clusters, len(texts) // 2))
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.9,
        max_features=5000,
    )
    X = vectorizer.fit_transform(texts)

    km = MiniBatchKMeans(
        n_clusters=k,
        random_state=seed,
        n_init=10,
        batch_size=64,
    )
    labels = km.fit_predict(X)
    terms = vectorizer.get_feature_names_out()

    clusters: list[WeaknessCluster] = []
    for cid in range(k):
        indices = [i for i, lab in enumerate(labels) if lab == cid]
        if not indices:
            continue
        centroid = km.cluster_centers_[cid]
        top_idx = centroid.argsort()[::-1][:8]
        top_terms = [str(terms[i]) for i in top_idx if centroid[i] > 0]

        sub_X = X[indices]
        dists = euclidean_distances(sub_X, centroid.reshape(1, -1)).flatten()
        exemplar_order = np.argsort(dists)[:3]
        exemplars = [texts[indices[int(i)]][:500] for i in exemplar_order]

        submission_ids = list({meta[i][0] for i in indices})
        clusters.append(
            WeaknessCluster(
                cluster_id=int(cid),
                size=len(indices),
                top_terms=top_terms,
                exemplars=exemplars,
                submission_ids=submission_ids,
            )
        )

    clusters.sort(key=lambda c: c.size, reverse=True)

    return WeaknessAggregate(
        venue_id=venue_id,
        n_submissions_sampled=len(sampled),
        n_weakness_texts=len(texts),
        n_clusters=len(clusters),
        clusters=clusters,
    ).model_dump()
