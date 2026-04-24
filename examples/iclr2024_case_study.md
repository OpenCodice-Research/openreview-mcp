# Case study: What gets papers rejected at ICLR 2024?

A reproducible analysis of 100 rejected ICLR 2024 submissions using
`openreview_aggregate_weaknesses`.

## Setup

```bash
pip install "openreview-mcp[analysis]"
```

```python
from openreview_mcp.client import OpenReviewClient
from openreview_mcp.tools import analysis

client = OpenReviewClient()

result = analysis.aggregate_weaknesses(
    client,
    venue_id="ICLR.cc/2024/Conference",
    sample_size=100,
    n_clusters=14,
    min_text_length=40,
    seed=7,
)
```

## Pipeline

The tool performs the following steps internally:

1. Fetch every ICLR 2024 submission (7,404) with embedded reviews and decisions.
2. Keep only submissions whose final decision contains `"reject"`.
3. Sample 100 rejected submissions with a fixed seed.
4. Extract the `weaknesses` field from every Official_Review.
5. Split each reviewer's weakness paragraph into individual bullet or numbered items, producing 1,361 per-complaint texts.
6. Vectorize with TF-IDF (sublinear TF, 1-2 grams, `min_df=3`, `max_df=0.5`).
7. Reduce to 64 latent dimensions via Truncated SVD.
8. Re-normalize and cluster with KMeans (`n_init=20`).

The tool returns each cluster's size, top TF-IDF terms, three nearest-to-centroid exemplars, and the contributing submission ids.

## Results

**Sample:** 100 submissions, 1,361 weakness items, 14 clusters.

| # | Size | Papers | Top terms | Interpretation |
|---|---:|---:|---|---|
| 13 | 197 | 79 | evaluation, tasks, work, performance, using, model | Evaluation setup is too narrow or biased |
|  2 | 194 | 66 | models, equation, model, assumption, information | Modeling choices and assumptions are unclear |
|  1 | 180 | 73 | experiments, authors, results, datasets, experimental | Experiments weak or theory shallow |
|  8 | 123 | 61 | method, proposed, unclear, authors, performance | Proposed method is heuristic or insufficiently validated |
|  9 | 104 | 55 | paper, lacks, main, weaknesses, iclr | Boilerplate "paper lacks X" statements |
|  3 |  88 | 43 | learning, federated, semi supervised, algorithm | Topic cluster: federated / semi-supervised |
| 11 |  83 | 51 | methods, existing, based, proposed | Insufficient comparison with prior work |
| 10 |  78 | 40 | section, authors, clarity, section authors | Typos, broken cross-references, minor writing bugs |
|  6 |  71 | 42 | et al, 2022, 2023, 2020 | Missing or incomplete citations |
|  7 |  68 | 32 | loss, eq, function, notation, training | Loss function and equation notation issues |
|  4 |  50 | 38 | figure, figures, clarity, fig, captions | Confusing figures or captions |
|  5 |  50 | 22 | time, time series, series, complexity | Topic cluster: time series |
|  0 |  44 | 34 | writing, presentation, improved, readability | Writing or presentation explicitly called out |
| 12 |  31 | 11 | https, org, html, pdf | Noise: URLs extracted from reviews |

## Exemplars

A representative complaint per top cluster (truncated to 250 characters).

**Cluster 13 (evaluation):**
> My main concerns with the paper are related to the framework's evaluation. I believe that the evaluation is quite limited and simplistic, given that the sample of the recruited participants is biased (...).

**Cluster 2 (modeling):**
> Overall, the description is unclear. For example, although the CDF plays a key role, the distribution of CDF is not explicitly written in the methodology section. In appendix, I found the authors used multi-task GP (...).

**Cluster 1 (experiments):**
> Weak Theoretical Results: I find the theoretical result to be weak, as it only considers the mixup of the labels. For appropriate analysis of the mixup, the mixing of data points (x) should also be considered (...).

**Cluster 8 (heuristic method):**
> In the proposed method, the initial seed generation and triplane selection seem to be quite heuristic in that the selections depend on the threshold.

**Cluster 11 (missing comparisons):**
> Though the authors claim that they aim to propose a unified framework, the methods considered in their paper are mainly based on AM and POMO, in other words, the auto-regressive methods. As far as I know, there are also other methods (...).

## Findings

1. **Evaluation dominates.** Clusters 13, 2, and 1 together account for 571 of 1,361 items (42%). The single largest rejection driver is not novelty, it is the perceived inadequacy of the experimental evaluation.

2. **Craftsmanship rejections are common.** Clusters 10 (typos), 4 (figures), 0 (writing), and 6 (citations) total 243 items from ~70 distinct papers. A substantial fraction of rejected papers carry explicit reviewer complaints about issues that are mechanical to fix before submission.

3. **Novelty is not the top-line reason.** The generic "paper lacks X" cluster (9) is only the fifth largest. Reviewers do raise novelty concerns, but they do so less often than they raise evaluation concerns.

4. **Topic-specific clusters emerge.** Federated learning (cluster 3) and time series (cluster 5) form their own clusters of size 88 and 50. These likely reflect both high submission volume in those areas and domain-specific failure modes.

## Limitations

- A 100-submission sample from a single venue in a single year. Patterns may not generalize.
- TF-IDF clustering captures lexical similarity, not semantic similarity; sentence-embedding approaches would likely surface different (probably finer) structure.
- The "URLs" noise cluster (12) is a reminder that the tool returns raw structure, not curated findings; a consuming agent should ignore such artifacts.
- We sample uniformly across all rejections; weighting by decision margin or reviewer confidence would bias the analysis toward stronger signals.

## Reproducing

```python
# Exact call used for this case study:
analysis.aggregate_weaknesses(
    client,
    venue_id="ICLR.cc/2024/Conference",
    sample_size=100,
    n_clusters=14,
    min_text_length=40,
    seed=7,
)
```

Fetching all submissions takes ~30s. Clustering is near-instant. Results are cached for 7 days under `~/.cache/openreview-mcp/`.
