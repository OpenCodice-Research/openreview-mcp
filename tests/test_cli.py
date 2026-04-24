"""CLI smoke tests (no server spin-up)."""

from __future__ import annotations

import pytest

from openreview_mcp import __version__
from openreview_mcp.cli import build_parser


def test_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.stdio is False
    assert args.http is False
    assert args.port == 8000


def test_parser_http_mode() -> None:
    args = build_parser().parse_args(["--http", "--port", "9001"])
    assert args.http is True
    assert args.port == 9001


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert __version__ in out
