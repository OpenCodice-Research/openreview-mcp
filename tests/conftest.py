"""Shared pytest fixtures.

Tests run offline: no real OpenReview calls. The `fake_client` fixture
returns a minimal stand-in for ``OpenReviewClient`` that returns pre-baked
notes, so tool logic (parsing, filtering, pydantic validation) can be
exercised without network.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any

import pytest

os.environ["OPENREVIEW_MCP_NO_CACHE"] = "1"


class _FakeV2:
    def __init__(self, notes: list[Any], groups: dict[str, Any] | None = None) -> None:
        self._notes = notes
        self._groups = groups or {}

    def get_all_notes(self, **_: Any) -> list[Any]:
        return self._notes

    def get_note(self, note_id: str) -> Any:
        for n in self._notes:
            if n.id == note_id:
                return n
        raise KeyError(note_id)

    def get_group(self, gid: str) -> Any:
        return self._groups.get(gid, SimpleNamespace(id=gid, members=[]))

    def get_profile(self, pid: str) -> Any:
        return SimpleNamespace(
            id=pid,
            content={
                "names": [{"fullname": "Jane Doe", "first": "Jane", "last": "Doe"}],
                "emails": ["jane@example.edu"],
                "history": [{"institution": {"name": "Example University"}}],
                "homepage": "https://example.edu/~jane",
                "orcid": "0000-0000-0000-0001",
            },
        )


class _FakeClient:
    def __init__(self, notes: list[Any], groups: dict[str, Any] | None = None) -> None:
        self.v2 = _FakeV2(notes, groups)
        self.v1 = self.v2

    def is_authenticated(self) -> bool:
        return False


def _make_note(
    note_id: str,
    *,
    forum: str | None = None,
    invitations: list[str] | None = None,
    content: dict[str, Any] | None = None,
    signatures: list[str] | None = None,
    cdate: int = 1_700_000_000_000,
    replyto: str | None = None,
) -> Any:
    return SimpleNamespace(
        id=note_id,
        forum=forum or note_id,
        invitations=invitations or [],
        content=content or {},
        signatures=signatures or ["~Anonymous1"],
        cdate=cdate,
        replyto=replyto,
        details={},
    )


@pytest.fixture
def make_note():
    return _make_note


@pytest.fixture
def fake_client():
    def _factory(notes: list[Any], groups: dict[str, Any] | None = None) -> _FakeClient:
        return _FakeClient(notes, groups=groups)

    return _factory
