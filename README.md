# openreview-mcp

**MCP server for [OpenReview](https://openreview.net)** — search submissions, fetch reviews, meta-reviews, rebuttals, and decisions from NeurIPS, ICLR, ACL ARR, COLM, TMLR, and any other venue hosted on OpenReview.

Built by [OpenCódice Research](https://github.com/OpenCodice-Research).

## Why

The academic MCP ecosystem covers arXiv (`academia-mcp`), Semantic Scholar, and HuggingFace, but the richest source of peer-review signal — **OpenReview** — is missing. This server exposes reviews, scores, area-chair decisions, and author rebuttals as MCP tools, enabling:

- **Reviewer-style critique agents** grounded in real reviewer language
- **Bibliography verification** for workshop and ARR venues
- **Weakness pattern analysis** across a venue/year ("what does NeurIPS 2025 tend to reject for?")
- **Meta-review study** for understanding area-chair decision patterns

## Tools

| Tool | Purpose |
|---|---|
| `openreview_list_venues` | List OpenReview venues, filterable by year or series |
| `openreview_venue_stats` | Acceptance rate and score distribution for a venue |
| `openreview_search_submissions` | Search papers by venue/query/author/keywords |
| `openreview_get_submission` | Full metadata + abstract + PDF URL for a submission |
| `openreview_search_by_author` | All submissions by an author profile |
| `openreview_get_reviews` | All reviews (scores, confidence, strengths, weaknesses) |
| `openreview_get_meta_review` | Area-chair meta-review and recommendation |
| `openreview_get_rebuttal` | Author responses to reviewers |
| `openreview_get_decision` | Accept/reject decision and comment |
| `openreview_get_profile` | Author profile, affiliation, publications |

## Install

```bash
pip install openreview-mcp
# or
uv add openreview-mcp
```

## Configuration

The server works out of the box for public venues. For access to venues requiring login:

```bash
export OPENREVIEW_USERNAME="you@example.com"
export OPENREVIEW_PASSWORD="..."
```

## Use with Claude Code

```bash
claude mcp add openreview -- openreview-mcp
```

## Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openreview": {
      "command": "openreview-mcp"
    }
  }
}
```

See [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json) for a full example.

## Run as HTTP server

```bash
openreview-mcp --http --port 8000
```

## Development

```bash
make install    # uv sync with dev extras
make test       # pytest (uses VCR cassettes, no network)
make lint       # ruff + mypy
make serve      # run HTTP server locally on :8000
```

## License

MIT — see [LICENSE](LICENSE).
