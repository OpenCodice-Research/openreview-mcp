---
title: "openreview-mcp: peer review as a queryable resource for LLMs"
subtitle: "Closing the biggest gap in the academic MCP stack, with a case study on ICLR 2024 to prove it."
date: 2026-04-24
author: OpenCódice Research
tags: [mcp, openreview, peer-review, research-tooling, iclr]
---

The Model Context Protocol ecosystem now covers most of an academic researcher's daily stack. There are MCP servers for arXiv, Semantic Scholar, Hugging Face datasets, Crossref, and Google Scholar. There is no MCP server for the most valuable corpus of all: peer review.

That is the gap [`openreview-mcp`](https://github.com/OpenCodice-Research/openreview-mcp) closes, and the reason we are open-sourcing it today.

## Why peer review

Most academic-search MCPs treat papers as the unit of information: title, abstract, citations, PDF. That is fine for discovery, but it ignores the densest signal that academic ML produces, which is the reasoning of expert reviewers explaining why a paper succeeds or fails.

OpenReview hosts that reasoning publicly for almost every major ML venue: ICLR, NeurIPS, COLM, TMLR, ACL ARR, and dozens of workshops. Reviews, author rebuttals, area-chair meta-reviews, and final decisions are all there, queryable through an official API. They are simply not reachable by any LLM you connect to today.

Until now.

## What `openreview-mcp` does

The server exposes eleven MCP tools that map cleanly onto OpenReview entities:

- **Venues**: list venues by year or series, compute submission and acceptance statistics for a venue.
- **Submissions**: search by venue, query, author, or keywords; fetch a single submission with its abstract and PDF link; list everything a profile has authored.
- **Reviews**: pull all official reviews for a submission with their ratings, confidence, soundness, presentation, contribution, summary, strengths, weaknesses, and questions.
- **Meta-reviews and decisions**: fetch the area-chair meta-review and the accept/reject decision separately.
- **Rebuttals**: pull author responses keyed to specific reviews.
- **Profiles**: resolve names, affiliations, and DBLP/ORCID/Scholar handles.
- **Aggregate weaknesses** (the signature tool): cluster recurrent reviewer complaints across a venue's rejections.

Install:

```bash
pip install "openreview-mcp[analysis]"
```

Wire it into Claude Code:

```bash
claude mcp add openreview -- openreview-mcp
```

Or Claude Desktop:

```json
{
  "mcpServers": {
    "openreview": { "command": "openreview-mcp" }
  }
}
```

Public venues work out of the box. Private venues read `OPENREVIEW_USERNAME` and `OPENREVIEW_PASSWORD` from the environment.

## The signature tool

`openreview_aggregate_weaknesses` is the differentiator. It samples rejected submissions from a venue, extracts every `weaknesses` paragraph from the official reviews, splits each paragraph into individual bullet or numbered items (reviewers usually list five to eight distinct complaints per review), vectorizes with TF-IDF, reduces with Truncated SVD to 64 latent dimensions, and clusters with KMeans.

The interesting design choice is that it does **not** return human-readable cluster labels. It returns each cluster's top TF-IDF terms, three nearest-to-centroid exemplars, and the contributing submission ids. The LLM that consumes the tool labels the clusters from the evidence.

This matters. A pre-baked taxonomy would freeze categories that vary across venues and years. A NeurIPS reviewer rejects papers for different reasons than an ACL reviewer. The fashionable failure modes shift over time. By returning raw clusters, we let the calling agent produce labels that are appropriate to whatever venue and slice of literature is being studied.

## Does it work? A case study on ICLR 2024

The honest test for a tool like this is whether it surfaces something non-obvious about a venue you already know well. So we pointed it at ICLR 2024.

```python
analysis.aggregate_weaknesses(
    client,
    venue_id="ICLR.cc/2024/Conference",
    sample_size=100,
    n_clusters=14,
    seed=7,
)
```

One hundred rejected submissions yielded 1,361 individual weakness statements clustered into 14 themes. The full table and exemplars live in [`examples/iclr2024_case_study.md`](https://github.com/OpenCodice-Research/openreview-mcp/blob/main/examples/iclr2024_case_study.md). Three results stood out.

**Evaluation, not novelty, drives most rejections.** The three largest clusters (197, 194, and 180 items) are all about the experimental setup: evaluation that is too narrow or biased, modeling choices that are unclear, and experiments or theory that are shallow. Together they account for 42% of all complaints. The generic "paper lacks novelty" cluster is only the fifth largest, with 104 items. This contradicts the folklore that novelty is the primary battleground.

**Craftsmanship still sinks papers.** Typos and broken cross-references (78 items), confusing figures and captions (50 items), missing citations (71 items), and explicit complaints about writing quality (44 items) together flag roughly 70 of the 100 sampled papers. Mechanical issues that a careful proof-reading pass would catch are routine reasons for rejection.

**Topic-specific failure modes emerge.** Federated learning and time series form their own clusters. Authors submitting in those areas would do well to read the cluster exemplars and pre-rebut the standard objections.

A reviewer's complaint from one of those clusters, copied unedited from the OpenReview record:

> Though the authors claim that they aim to propose a unified framework, the methods considered in their paper are mainly based on AM and POMO, in other words, the auto-regressive methods. As far as I know, there are also other methods (...).

This kind of specificity is what `aggregate_weaknesses` surfaces as evidence. Not abstract categories, the actual language and detail that rejected papers faced.

## What this enables

- **Pre-submission self-review.** Run the tool on your target venue. Ask your LLM which clusters your draft is most exposed to, and harden those sections before reviewers find them.
- **Reviewer-style critique agents.** Ground a harsh-reviewer agent on real reviewer language from the target venue, not on a generic rubric.
- **Teaching.** Show PhD students what a venue actually rejects papers for, with evidence.
- **Rebuttal mining.** Pair `get_rebuttal` with `get_decision` to study which rebuttal patterns flipped borderline rejections into acceptances.

## What is next

`openreview-mcp` is the first MCP server we ship from OpenCódice Research. Two more are on the runway: a deadline tracker for academic CFPs, and a Zenodo bridge for dataset and code deposits with DOIs.

The repository is [github.com/OpenCodice-Research/openreview-mcp](https://github.com/OpenCodice-Research/openreview-mcp). Issues and pull requests are welcome. We are particularly interested in contributions that add sentence-embedding clustering as an alternative to TF-IDF, venue-specific normalization for non-standard review templates, and a public dashboard refreshed weekly for the largest venues.

If you build something on top of it, tell us. We will link to it.

---

*OpenCódice Research builds open tooling for academic workflows. We started with the most under-served corpus in the LLM stack and we are working outward.*
