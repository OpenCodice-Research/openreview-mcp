# Contributing to openreview-mcp

Thanks for considering a contribution. Issues and pull requests are welcome.

## Setup

```bash
git clone https://github.com/OpenCodice-Research/openreview-mcp.git
cd openreview-mcp
uv sync --all-extras   # or: pip install -e ".[dev,analysis]"
```

## Running the test suite

```bash
make test          # pytest, offline (uses a fake OpenReview client)
make lint          # ruff check + mypy
make fmt           # ruff format + autofix
```

The test suite is fully offline — it never hits the OpenReview API. New
tests should also be offline; use the `fake_client` and `make_note`
fixtures in `tests/conftest.py`.

## Development against a real OpenReview venue

```bash
OPENREVIEW_MCP_NO_CACHE=1 python -c "
from openreview_mcp.client import OpenReviewClient
from openreview_mcp.tools import submissions
print(submissions.search_submissions(OpenReviewClient(), 'ICLR.cc/2024/Conference', limit=3))
"
```

For private venues set `OPENREVIEW_USERNAME` and `OPENREVIEW_PASSWORD`.

## Pull request checklist

- [ ] `make lint` passes (ruff + mypy strict)
- [ ] `make test` passes (pytest, all offline)
- [ ] `make fmt` has been run
- [ ] The change is described in `CHANGELOG.md` under `## [Unreleased]`
- [ ] Public-facing behaviour changes are reflected in `README.md`

## Areas where contributions are particularly welcome

- Sentence-embedding clustering as an alternative to TF-IDF in `aggregate_weaknesses`.
- Venue-specific normalisation profiles (TMLR, ARR cycles, niche workshops).
- Additional tools that surface signal from OpenReview (e.g. reviewer-tenure analysis, decision-margin analysis).

## Releases

Releases are cut by tagging `vX.Y.Z` from `main`. The release workflow
publishes to PyPI via Trusted Publishing and creates a GitHub Release
with notes from `CHANGELOG.md`.

## License

By contributing you agree that your contributions are licensed under the
MIT License (see `LICENSE`).
