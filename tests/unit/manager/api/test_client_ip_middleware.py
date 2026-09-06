from __future__ import annotations

from unittest.mock import MagicMock

from aiohttp import web

from ai.backend.common.contexts.client_ip import current_client_ip
from ai.backend.manager.api.rest.middleware.auth import (
    TRUSTED_PROXY_NETWORKS_KEY,
    parse_trusted_proxy_networks,
)
from ai.backend.manager.api.rest.middleware.client_ip import client_ip_middleware

CLIENT = "203.0.113.7"
TRUSTED_PROXY = "10.0.0.1"


def _make_request(
    *,
    peer: str | None = CLIENT,
    forwarded_for: str | None = None,
    trusted_proxies: list[str] | None = None,
) -> web.Request:
    request = MagicMock(spec=web.Request)
    request.headers = {} if forwarded_for is None else {"X-Forwarded-For": forwarded_for}
    request.remote = peer
    request.config_dict = {
        TRUSTED_PROXY_NETWORKS_KEY: parse_trusted_proxy_networks(trusted_proxies or [])
    }
    if peer is None:
        request.transport = None
    else:
        transport = MagicMock()
        transport.get_extra_info.return_value = (peer, 54321)
        request.transport = transport
    return request


async def _run(request: web.Request) -> str | None:
    seen: list[str | None] = []

    async def handler(_: web.Request) -> web.StreamResponse:
        seen.append(current_client_ip())
        return web.Response()

    await client_ip_middleware(request, handler)
    return seen[0]


async def test_the_handler_sees_the_client_ip() -> None:
    """The middleware runs before authentication, so a login attempt carries its address."""
    assert await _run(_make_request()) == CLIENT


async def test_the_address_is_resolved_through_the_trusted_proxy_chain() -> None:
    request = _make_request(
        peer=TRUSTED_PROXY,
        forwarded_for=f"{CLIENT}, {TRUSTED_PROXY}",
        trusted_proxies=[TRUSTED_PROXY],
    )

    assert await _run(request) == CLIENT


async def test_a_request_without_an_address_leaves_the_context_empty() -> None:
    assert await _run(_make_request(peer=None)) is None


async def test_the_client_ip_does_not_leak_past_the_request() -> None:
    await _run(_make_request())

    assert current_client_ip() is None
