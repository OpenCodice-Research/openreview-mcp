---
title: "What ICLR reviewers actually complain about"
subtitle: "A data-driven look at 1,361 weaknesses from 100 rejected ICLR 2024 papers"
date: 2026-04-24
author: OpenCódice Research
tags: [peer-review, MCP, openreview, research-tooling, iclr]
---

Ask any senior researcher why papers get rejected at top ML conferences and you will hear a familiar list: *"not novel enough", "writing needs work", "not the right venue"*. This folklore shapes how people revise papers, pitch to PhD students, and benchmark themselves against the field.

We decided to check the folklore against data.

## The question

What, exactly, do ICLR reviewers write in the `weaknesses` section of their reviews? If we pulled 100 rejected papers, extracted every weakness statement, and clustered them, what would the biggest categories turn out to be?

To make this easy we first needed a way to query OpenReview programmatically and feed reviews to an LLM. That turned out to be the missing piece in the academic MCP (Model Context Protocol) ecosystem, so we built it:

**[`openreview-mcp`](https://github.com/OpenCodice-Research/openreview-mcp)** is an MCP server that exposes OpenReview submissions, reviews, rebuttals, meta-reviews, and decisions as tools any LLM can call. The repository is MIT-licensed and the install is `pip install "openreview-mcp[analysis]"`.

## The experiment

Using the server's `openreview_aggregate_weaknesses` tool, we ran:

```python
analysis.aggregate_weaknesses(
    client,
    venue_id="ICLR.cc/2024/Conference",
    sample_size=100,
    n_clusters=14,
    seed=7,
)
```

The tool samples 100 rejected submissions, splits each reviewer's weakness paragraph into individual bullet or numbered items (reviewers tend to list 5-8 distinct complaints per review), vectorizes them with TF-IDF, reduces to 64 latent dimensions, and clusters with KMeans.

The sample yielded **1,361 individual weakness statements**. Fourteen clusters emerged.

## The findings

### The single biggest rejection driver is evaluation, not novelty

The three largest clusters (42% of all complaints) are about the experimental setup: evaluation is too narrow or biased (cluster 13, 197 items), modeling choices and assumptions are unclear (cluster 2, 194 items), and experiments or theory are shallow (cluster 1, 180 items).

The generic "paper lacks novelty" cluster is only the fifth largest, with 104 items. Reviewers do raise novelty concerns, but much less frequently than they raise evaluation concerns.

This upends the folklore. If you are optimizing your paper against imagined reviewer objections, you should probably worry less about whether your contribution sounds novel enough in the introduction, and more about whether your evaluation is thorough enough to withstand a skeptic.

### Craftsmanship still sinks papers

Typos and broken cross-references (cluster 10, 78 items), confusing figures and captions (cluster 4, 50 items), missing citations (cluster 6, 71 items), and explicit complaints about writing quality (cluster 0, 44 items) together account for 243 items from roughly 70 distinct papers.

These are mechanical issues. They can be fixed with a proof-reading pass, a careful look at the figures, and a reference sweep before submission. And yet a large fraction of rejected papers carry explicit reviewer callouts for exactly these issues. Peer review is not blind to polish.

### Topic-specific failure modes

Two clusters are narrowly topical: federated and semi-supervised learning (cluster 3, 88 items) and time series (cluster 5, 50 items). These likely reflect both high submission volume and domain-specific failure modes (e.g. unrealistic non-IID data settings for federated work). Authors submitting to these areas would do well to read the cluster exemplars and pre-rebut the standard complaints.

### The representative quote

A single line from cluster 11 (insufficient comparisons) captures how reviewers actually write:

> Though the authors claim that they aim to propose a unified framework, the methods considered in their paper are mainly based on AM and POMO, in other words, the auto-regressive methods. As far as I know, there are also other methods (...).

Notice how specific this is. The reviewer is not saying "not enough comparisons", they are naming the exact families of methods the paper ignores. This is what the `aggregate_weaknesses` tool surfaces as evidence: not abstract categories, but the actual language and specificity that rejected papers faced.

## Why this matters

A large amount of research advice is passed down through folklore. PhD advisors tell students what to watch out for, based on what they remember from their own submissions. The memory is real, but it is a biased sample.

With peer reviews now public on OpenReview for the major ML venues, the honest move is to go look at what reviewers actually wrote. Thousands of reviews, aggregated and clustered, are a better evidence base than a senior researcher's recollection of their last rejection.

The catch is that nobody reads 10,000 reviews by hand. You need tooling. That is why we wrote `openreview-mcp`, and why its signature tool returns raw clusters and evidence rather than pre-baked conclusions: the consuming agent (Claude, in our case) labels the clusters from the exemplars, and the labels change appropriately when you query a different venue, a different year, or a different subfield.

## What to use it for

- **Pre-submission self-review.** Run `aggregate_weaknesses` on your target venue before submitting. Ask your LLM to identify which complaint clusters your draft is most vulnerable to, and strengthen those sections before reviewers notice.
- **Reviewer-style critique agents.** Ground a harsh-reviewer agent on real reviewer language from the target venue, not on a generic rubric. A NeurIPS reviewer and an ACL reviewer do not reject papers for the same reasons.
- **Teaching.** Show PhD students what a venue actually cares about, with evidence.
- **Rebuttal mining.** Pair `get_rebuttal` with `get_decision` to study which rebuttal patterns converted borderline rejections into acceptances.

## Try it

The server runs under any MCP-compatible client. For Claude Desktop:

```json
{
  "mcpServers": {
    "openreview": {
      "command": "openreview-mcp"
    }
  }
}
```

For Claude Code:

```bash
claude mcp add openreview -- openreview-mcp
```

Once connected, ask: *"Cluster the weaknesses in 100 rejected ICLR 2024 papers and tell me what reviewers actually care about."* The MCP does the work.

Repository: [github.com/OpenCodice-Research/openreview-mcp](https://github.com/OpenCodice-Research/openreview-mcp).

Issues and pull requests welcome. We are particularly interested in contributions that add venue-specific normalization, sentence-embedding clustering, and a weekly-refreshed public dashboard of the largest venues.

---

*OpenCódice Research builds open tooling for academic workflows. `openreview-mcp` is the first of a planned series of MCP servers covering the gaps in the scientific-research LLM stack.*
