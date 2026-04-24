"""Aggregate analysis across a venue's reviews.

This module's signature tool, ``aggregate_weaknesses``, samples rejected
submissions from a venue, splits each reviewer's weakness paragraph into
individual items (bullets, numbered points), vectorizes with TF-IDF,
reduces via Truncated SVD (LSA), and clusters with KMeans to surface
recurrent complaint themes.

Clusters are returned as raw top-terms + exemplars, not pre-labelled: the
LLM consuming this MCP is expected to label them itself from the evidence,
which avoids baking a fixed taxonomy into the server.
"""

from __future__ import annotations

import random
import re
from typing import Any

from ..cache import cached
from ..client import OpenReviewClient
from ..schemas import WeaknessAggregate, WeaknessCluster
from ._helpers import content_value

# Matches common weakness-item delimiters at the start of a line:
#   "- ...", "* ...", "• ...", "1. ...", "1) ...", "(1) ...",
#   "W1. ...", "Q2. ...", "###  ..."
_ITEM_SPLIT_RE = re.compile(
    r"(?m)^\s*(?:[-*•]|\d+[.)]|\(\d+\)|[WQwq]\d+[.)]|#{1,6})\s+",
)


_SKLEARN_ERROR = (
    "openreview_aggregate_weaknesses requires scikit-learn. "
    "Install with `pip install openreview-mcp[analysis]`."
)


def _require_sklearn() -> tuple[Any, Any, Any, Any, Any, Any]:
    """Lazy-import sklearn + numpy. Raise a clear error if the extra is missing."""
    try:
        import numpy as np
        from sklearn.cluster import KMeans
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import euclidean_distances
        from sklearn.preprocessing import Normalizer
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(_SKLEARN_ERROR) from e
    return TfidfVectorizer, TruncatedSVD, Normalizer, KMeans, euclidean_distances, np


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


def _split_items(text: str) -> list[str]:
    """Split a weakness paragraph into individual items (bullets, numbered, etc.).

    Falls back to the whole text if no delimiters are found.
    """
    pieces = _ITEM_SPLIT_RE.split(text)
    items = [p.strip() for p in pieces if p and p.strip()]
    return items or [text.strip()]


def _extract_weaknesses(note: Any, split_items: bool) -> list[tuple[str, str, str]]:
    """Return ``(submission_id, reviewer_id, weakness_text)`` triples.

    If ``split_items`` is true, each reviewer's weakness paragraph is split
    into individual bullet/numbered items — this greatly reduces within-review
    vocabulary overlap and yields much cleaner clusters.
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
        chunks = _split_items(text) if split_items else [text.strip()]
        for chunk in chunks:
            out.append((note.id, signatures[0], chunk))
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
    split_items: bool = True,
) -> dict[str, Any]:
    """Cluster recurrent weakness themes across a venue's (typically rejected) reviews.

    Each reviewer's weakness paragraph is split into individual bullet or numbered
    items (disable with ``split_items=False``). Items are then vectorized with
    TF-IDF, reduced to 64 latent dimensions with Truncated SVD (LSA), re-normalized,
    and clustered with KMeans — a classic pipeline that separates text much better
    than KMeans on raw sparse TF-IDF.
    """
    TfidfVectorizer, TruncatedSVD, Normalizer, KMeans, euclidean_distances, np = _require_sklearn()

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
        for sub_id, reviewer_id, text in _extract_weaknesses(note, split_items=split_items):
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
        min_df=3,
        max_df=0.5,
        max_features=10000,
        sublinear_tf=True,
        norm="l2",
    )
    X_sparse = vectorizer.fit_transform(texts)

    # LSA to 64 dims (or as many as the data supports) dramatically improves
    # cluster separation vs raw sparse TF-IDF.
    n_components = min(64, X_sparse.shape[1] - 1, X_sparse.shape[0] - 1)
    if n_components >= 2:
        svd = TruncatedSVD(n_components=n_components, random_state=seed)
        normalizer = Normalizer(copy=False)
        X = normalizer.fit_transform(svd.fit_transform(X_sparse))
    else:
        X = X_sparse.toarray()

    km = KMeans(
        n_clusters=k,
        random_state=seed,
        n_init=20,
    )
    labels = km.fit_predict(X)
    terms = vectorizer.get_feature_names_out()

    # Compute top TF-IDF terms per cluster directly from member docs
    # (LSA-space centroids don't map back to terms cleanly).
    def _top_terms_for(indices: list[int]) -> list[str]:
        mean_tfidf = X_sparse[indices].mean(axis=0)
        # mean_tfidf is a 1xV numpy matrix — flatten, then rank.
        arr = np.asarray(mean_tfidf).flatten()
        top_idx = arr.argsort()[::-1][:8]
        return [str(terms[i]) for i in top_idx if arr[i] > 0]

    clusters: list[WeaknessCluster] = []
    for cid in range(k):
        indices = [i for i, lab in enumerate(labels) if lab == cid]
        if not indices:
            continue
        top_terms = _top_terms_for(indices)

        centroid = km.cluster_centers_[cid]
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
