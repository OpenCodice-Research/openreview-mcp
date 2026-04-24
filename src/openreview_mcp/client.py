"""Thin wrapper around openreview-py.

OpenReview operates two API generations in parallel:
- v1 (``api.openreview.net``) — legacy invitations, pre-2023 venues
- v2 (``api2.openreview.net``) — current default, used by all new venues

Modern venues (NeurIPS 2023+, ICLR 2024+, ACL ARR, COLM) live on v2. This
wrapper defaults to v2 and falls back to v1 on demand.
"""

from __future__ import annotations

import logging
import os
from functools import cached_property
from typing import Any

import openreview  # type: ignore[import-untyped]

log = logging.getLogger(__name__)

API_V2_URL = "https://api2.openreview.net"
API_V1_URL = "https://api.openreview.net"


class OpenReviewClient:
    """Lazy, credential-aware wrapper around ``openreview.api.OpenReviewClient``.

    Credentials are read from ``OPENREVIEW_USERNAME`` / ``OPENREVIEW_PASSWORD``
    if present; otherwise the client runs anonymously and can only access
    public venues and public notes.
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._username = username or os.environ.get("OPENREVIEW_USERNAME")
        self._password = password or os.environ.get("OPENREVIEW_PASSWORD")

    @cached_property
    def v2(self) -> Any:
        """OpenReview v2 API client."""
        return openreview.api.OpenReviewClient(
            baseurl=API_V2_URL,
            username=self._username,
            password=self._password,
        )

    @cached_property
    def v1(self) -> Any:
        """OpenReview v1 API client (legacy venues)."""
        return openreview.Client(
            baseurl=API_V1_URL,
            username=self._username,
            password=self._password,
        )

    def is_authenticated(self) -> bool:
        return bool(self._username and self._password)
