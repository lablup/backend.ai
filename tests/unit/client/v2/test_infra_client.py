"""Regression tests for #11957.

``InfraClient.get_wsproxy_version`` is a GET whose manager handler parses the
``group`` parameter from the query string (``QueryParam[WsproxyVersionQueryParam]``).
The request DTO must therefore be serialized into the query string, never the JSON
body — otherwise the ``group`` access-control filter is silently dropped.
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
from ai.backend.client.v2.domains.infra import InfraClient
from ai.backend.common.dto.manager.infra import GetWSProxyVersionRequest


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
    """A mock aiohttp session whose ``request`` returns a valid wsproxy-version body."""
    session = MagicMock(spec=aiohttp.ClientSession)
    session.request = MagicMock(return_value=_FakeResponse(200, {"wsproxy_version": 2}))
    return session


@pytest.fixture
def infra_client(captured_session: aiohttp.ClientSession) -> InfraClient:
    config = ClientConfig(endpoint=URL("http://localhost:8090"))
    client = BackendAIAuthClient(config, FakeAuth(), captured_session)
    return InfraClient(client)


async def test_get_wsproxy_version_sends_group_as_query_param_not_body(
    infra_client: InfraClient,
    captured_session: aiohttp.ClientSession,
) -> None:
    await infra_client.get_wsproxy_version(
        "default",
        GetWSProxyVersionRequest(group="research"),
    )

    _, kwargs = captured_session.request.call_args
    assert kwargs["json"] is None
    assert kwargs["params"] == {"group": "research"}


async def test_get_wsproxy_version_serializes_uuid_group_to_query_string(
    infra_client: InfraClient,
    captured_session: aiohttp.ClientSession,
) -> None:
    group_id = UUID("22222222-2222-2222-2222-222222222222")
    await infra_client.get_wsproxy_version(
        "default",
        GetWSProxyVersionRequest(group=group_id),
    )

    _, kwargs = captured_session.request.call_args
    assert kwargs["json"] is None
    assert kwargs["params"] == {"group": str(group_id)}


async def test_get_wsproxy_version_without_request_sends_no_params(
    infra_client: InfraClient,
    captured_session: aiohttp.ClientSession,
) -> None:
    await infra_client.get_wsproxy_version("default")

    _, kwargs = captured_session.request.call_args
    assert kwargs["json"] is None
    assert kwargs["params"] is None
