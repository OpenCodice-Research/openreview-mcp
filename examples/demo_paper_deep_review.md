# Demo: grounding a reviewer-style agent on real OpenReview data

This example shows how `openreview-mcp` pairs with a "harsh reviewer" agent
(e.g. the `paper-deep-review` skill) by grounding critique on the actual
language reviewers used in a venue.

## 1. Pick a venue and sample its reviews

> List NeurIPS 2025 decisions and pull reviews from 10 rejected papers so I can
> see what kinds of weaknesses sank them.

The agent calls:

- `openreview_list_venues(year=2025, series="NeurIPS")`
- `openreview_venue_stats(venue_id="NeurIPS.cc/2025/Conference")`
- `openreview_search_submissions(venue_id="NeurIPS.cc/2025/Conference", limit=200)`
- For each rejected id: `openreview_get_reviews(submission_id=...)` + `openreview_get_decision(...)`

## 2. Let the agent cluster weaknesses

With the review texts in context, the agent can cluster recurrent complaints:
missing baselines, unclear novelty, insufficient ablations, unrealistic
assumptions, reproducibility issues.

## 3. Run `paper-deep-review` on your draft

The reviewer agent now critiques your manuscript using the same vocabulary and
threshold that actually rejected papers at that venue — not a generic rubric.

## 4. Rebuttal mining

> How did authors of 3 borderline-accepted NeurIPS 2024 papers rebut concerns
> about missing baselines?

- `openreview_search_submissions(...)` filtering by decision
- `openreview_get_rebuttal(submission_id=...)` for each

This gives concrete, successful rebuttal patterns to reuse.
