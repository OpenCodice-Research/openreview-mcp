"""CLI entrypoint for the openreview-mcp server."""

from __future__ import annotations

import argparse
import logging
import sys

from . import __version__
from .server import mcp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openreview-mcp",
        description="MCP server for OpenReview (reviews, rebuttals, decisions).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    transport = parser.add_mutually_exclusive_group()
    transport.add_argument(
        "--stdio",
        action="store_true",
        help="Run over stdio transport (default).",
    )
    transport.add_argument(
        "--http",
        action="store_true",
        help="Run over streamable HTTP transport.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000).")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.http:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
