"""Regression tests for #11955.

``get_container_logs`` / ``get_status_history`` / ``get_commit_status`` are GET
requests whose manager handlers parse parameters from the query string
(``QueryParam``). The request DTO must therefore be serialized into the query
string, never the JSON body — otherwise fields like ``owner_access_key`` are
silently dropped and a privileged delegated read 404s.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

import aiohttp
import pytest
from yarl import URL

from ai.backend.client.v2.auth import AuthStrategy
from ai.backend.client.v2.base_client import BackendAIAuthClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.session import SessionClient
from ai.backend.common.dto.manager.session.request import (
    GetCommitStatusRequest,
    GetContainerLogsRequest,
    GetStatusHistoryRequest,
)


class FakeAuth(AuthStrategy):
    def sign(
        self,
        method: str,
        version: str,
        endpoint: URL,
        date: datetime,
        rel_url: str,
        content_type: str,
    ) -> Mapping[str, str]:
        return {"Authorization": "Fake fake-key:fake-sig"}


class _FakeResponse:
    """Minimal stand-in for an aiohttp response used as an async context manager."""

    def __init__(self, status: int, payload: dict[str, Any]) -> None:
        self.status = status
        self.reason = "OK"
        self._payload = payload

    async def json(self) -> dict[str, Any]:
        return self._payload

    async def __aenter__(self) -> _FakeResponse:
        return self

    async def __aexit__(self, *args: object) -> bool:
        return False


@pytest.fixture
def captured_session() -> aiohttp.ClientSession:
    """A mock aiohttp session whose ``request`` returns a 200 with an empty body."""
    session = MagicMock(spec=aiohttp.ClientSession)
    session.request = MagicMock(return_value=_FakeResponse(200, {}))
    return session


@pytest.fixture
def session_client(captured_session: aiohttp.ClientSession) -> SessionClient:
    config = ClientConfig(endpoint=URL("http://localhost:8090"))
    client = BackendAIAuthClient(config, FakeAuth(), captured_session)
    return SessionClient(client)


async def test_get_container_logs_sends_query_params_not_body(
    session_client: SessionClient,
    captured_session: aiohttp.ClientSession,
) -> None:
    kernel_id = UUID("11111111-1111-1111-1111-111111111111")
    await session_client.get_container_logs(
        "sess-1",
        GetContainerLogsRequest(owner_access_key="AKIATEST", kernel_id=kernel_id),
    )

    _, kwargs = captured_session.request.call_args
    assert kwargs["json"] is None
    assert kwargs["params"] == {
        "owner_access_key": "AKIATEST",
        "kernel_id": str(kernel_id),
    }


async def test_get_status_history_sends_query_params_not_body(
    session_client: SessionClient,
    captured_session: aiohttp.ClientSession,
) -> None:
    await session_client.get_status_history(
        "sess-1",
        GetStatusHistoryRequest(owner_access_key="AKIATEST"),
    )

    _, kwargs = captured_session.request.call_args
    assert kwargs["json"] is None
    assert kwargs["params"] == {"owner_access_key": "AKIATEST"}


async def test_get_commit_status_sends_query_params_not_body(
    session_client: SessionClient,
    captured_session: aiohttp.ClientSession,
) -> None:
    await session_client.get_commit_status(
        "sess-1",
        GetCommitStatusRequest(login_session_token="tok-123"),
    )

    _, kwargs = captured_session.request.call_args
    assert kwargs["json"] is None
    assert kwargs["params"] == {"login_session_token": "tok-123"}


async def test_get_container_logs_without_request_sends_no_params(
    session_client: SessionClient,
    captured_session: aiohttp.ClientSession,
) -> None:
    await session_client.get_container_logs("sess-1")

    _, kwargs = captured_session.request.call_args
    assert kwargs["json"] is None
    assert kwargs["params"] is None
