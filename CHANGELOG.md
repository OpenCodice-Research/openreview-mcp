# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-25

Initial release.

### Added
- MCP server exposing eleven tools across four entity families plus an analysis tool.
  - **Venues**: `openreview_list_venues`, `openreview_venue_stats`.
  - **Submissions**: `openreview_search_submissions`, `openreview_get_submission`, `openreview_search_by_author`.
  - **Reviews**: `openreview_get_reviews`, `openreview_get_meta_review`, `openreview_get_rebuttal`, `openreview_get_decision`.
  - **Profiles**: `openreview_get_profile`.
  - **Analysis**: `openreview_aggregate_weaknesses` (TF-IDF + Truncated SVD + KMeans clustering of recurrent reviewer complaints across a venue's rejections).
- `stdio` and `streamable-http` transports via the `openreview-mcp` CLI entry point.
- Optional `analysis` extra (`scikit-learn`, `numpy`) for the clustering tool.
- Disk-backed TTL cache (`diskcache`) keyed per-tool, bypassable with `OPENREVIEW_MCP_NO_CACHE=1`.
- Pydantic v2 schemas for every returned entity.
- `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD` support for venues that require authentication.
- 20 offline tests with a fake OpenReview client; CI matrix on Python 3.11 and 3.12.
- ICLR 2024 case study (`examples/iclr2024_case_study.md`) with a 100-submission, 14-cluster reproducible analysis.
- Companion launch post (`blog/2026-04-24-openreview-mcp.md`) and design rationale.

### Documentation
- OpenCódice Technical Report **OC-TR-2026-007** documents the architecture, analysis pipeline, and case study. Available on [Zenodo](https://zenodo.org/records/19758460), DOI [`10.5281/zenodo.19758460`](https://doi.org/10.5281/zenodo.19758460).

[Unreleased]: https://github.com/OpenCodice-Research/openreview-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/OpenCodice-Research/openreview-mcp/releases/tag/v0.1.0
