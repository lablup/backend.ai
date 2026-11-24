from __future__ import annotations

from functools import partial
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl
from aiohttp import web
from pytest_mock import MockerFixture

from ai.backend.common.clients.http_client.client_pool import ClientPool, tcp_client_session_factory
<<<<<<< HEAD
from ai.backend.web.auth import get_anonymous_session, get_api_session
from ai.backend.web.clients.endpoint_pool import AcquiredEndpoint
=======
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.endpoint_pool.types import AcquiredEndpoint
from ai.backend.common.middlewares.request_id import REQUEST_ID_HEADER, request_id_middleware
from ai.backend.common.types import ReadableCIDR
from ai.backend.web.auth import (
    TRUSTED_PROXY_NETWORKS_KEY,
    build_forwarding_headers,
    get_anonymous_session,
    get_api_session,
    get_client_ip,
)
>>>>>>> 8f2af8dd6 (fix(BA-7374): trust X-Forwarded-For only from configured proxies in the webserver (#17265))

from .conftest import DummyApiConfig, DummyConfig


class DummyRequest:
    def __init__(self, app_data: dict[str, Any]) -> None:
        self.app = app_data


@pytest.fixture
async def client_pool() -> ClientPool:
    factory = partial(
        tcp_client_session_factory,
        ssl=False,
        limit=10,
        limit_per_host=5,
    )
    return ClientPool(factory, cleanup_interval_seconds=100)


async def test_get_api_session(mocker: MockerFixture, client_pool: ClientPool) -> None:
    mock_request = DummyRequest({
        "config": DummyConfig(
            DummyApiConfig(
                domain="default",
                endpoint=[yarl.URL("https://api.backend.ai")],
                ssl_verify=False,
            )
        ),
        "client_pool": client_pool,
    })

    acquired = AcquiredEndpoint(endpoint="https://api.backend.ai")

    mock_get_session = AsyncMock(
        return_value={
            "authenticated": False,
        }
    )
    mocker.patch("ai.backend.web.auth.get_session", mock_get_session)
    with pytest.raises(web.HTTPUnauthorized):
        await get_api_session(cast(Any, mock_request), acquired)
    mock_get_session.assert_awaited_once()

    mock_get_session = AsyncMock(
        return_value={
            "authenticated": True,
            "token": {"type": "something-else"},
        }
    )
    mocker.patch("ai.backend.web.auth.get_session", mock_get_session)
    with pytest.raises(web.HTTPBadRequest):
        await get_api_session(cast(Any, mock_request), acquired)
    mock_get_session.assert_awaited_once()

    mock_get_session = AsyncMock(
        return_value={
            "authenticated": True,
            "token": {"type": "keypair", "access_key": "ABC", "secret_key": "xyz"},
        }
    )
    mocker.patch("ai.backend.web.auth.get_session", mock_get_session)
    api_session = await get_api_session(cast(Any, mock_request), acquired)
    mock_get_session.assert_awaited_once()
    async with api_session:
        assert not api_session.config.is_anonymous
        assert api_session.config.domain == "default"
        assert str(api_session.config.endpoint) == "https://api.backend.ai"
        assert api_session.config.access_key == "ABC"
        assert api_session.config.secret_key == "xyz"


async def test_get_api_session_with_specific_api_endpoint(
    mocker: MockerFixture, client_pool: ClientPool
) -> None:
    mock_request = DummyRequest({
        "config": DummyConfig(
            DummyApiConfig(
                domain="default",
                endpoint=[yarl.URL("https://api.backend.ai")],
                ssl_verify=False,
            )
        ),
        "client_pool": client_pool,
    })
    mock_get_session = AsyncMock(
        return_value={
            "authenticated": True,
            "token": {"type": "keypair", "access_key": "ABC", "secret_key": "xyz"},
        }
    )
    specific_api_endpoint = "https://alternative.backend.ai"
    mocker.patch("ai.backend.web.auth.get_session", mock_get_session)
    api_session = await get_api_session(
        cast(Any, mock_request),
        AcquiredEndpoint(endpoint=specific_api_endpoint),
    )
    mock_get_session.assert_awaited_once()
    async with api_session:
        assert str(api_session.config.endpoint) == specific_api_endpoint


async def test_get_anonymous_session(mocker: MockerFixture, client_pool: ClientPool) -> None:
    mock_request = DummyRequest({
        "config": DummyConfig(
            DummyApiConfig(
                domain="default",
                endpoint=[yarl.URL("https://api.backend.ai")],
                ssl_verify=False,
            )
        ),
        "client_pool": client_pool,
    })
    mock_get_session = MagicMock()
    mocker.patch("ai.backend.web.auth.get_session", mock_get_session)
    api_session = await get_anonymous_session(
        cast(Any, mock_request),
        AcquiredEndpoint(endpoint="https://api.backend.ai"),
    )
    mock_get_session.assert_not_called()
    async with api_session:
        assert api_session.config.is_anonymous
        assert api_session.config.domain == "default"
        assert str(api_session.config.endpoint) == "https://api.backend.ai"
        assert api_session.config.access_key == ""
        assert api_session.config.secret_key == ""


async def test_get_anonymous_session_with_specific_api_endpoint(
    mocker: MockerFixture, client_pool: ClientPool
) -> None:
    mock_request = DummyRequest({
        "config": DummyConfig(
            DummyApiConfig(
                domain="default",
                endpoint=[yarl.URL("https://api.backend.ai")],
                ssl_verify=False,
            )
        ),
        "client_pool": client_pool,
    })
    specific_api_endpoint = "https://alternative.backend.ai"
    mock_get_session = MagicMock()
    mocker.patch("ai.backend.web.auth.get_session", mock_get_session)
    api_session = await get_anonymous_session(
        cast(Any, mock_request),
        AcquiredEndpoint(endpoint=specific_api_endpoint),
    )
    mock_get_session.assert_not_called()
    async with api_session:
        assert str(api_session.config.endpoint) == specific_api_endpoint
<<<<<<< HEAD
=======


def _create_forwarding_app() -> web.Application:
    async def handler(request: web.Request) -> web.Response:
        return web.json_response({
            "forwarded": build_forwarding_headers(request).get(REQUEST_ID_HEADER),
            "current": current_request_id(),
        })

    app = web.Application(middlewares=[request_id_middleware])
    app.router.add_get("/", handler)
    return app


async def test_forwarding_headers_carry_incoming_request_id(aiohttp_client: Any) -> None:
    client = await aiohttp_client(_create_forwarding_app())
    request_id = str(uuid.uuid4())

    resp = await client.get("/", headers={REQUEST_ID_HEADER: request_id})

    body = await resp.json()
    assert body["forwarded"] == request_id


async def test_forwarding_headers_carry_generated_request_id(aiohttp_client: Any) -> None:
    client = await aiohttp_client(_create_forwarding_app())

    resp = await client.get("/")

    body = await resp.json()
    assert body["forwarded"] is not None
    assert body["forwarded"] == body["current"]


def test_forwarding_headers_omit_request_id_outside_request_scope() -> None:
    request = make_mocked_request("GET", "/", headers={"X-Forwarded-For": "10.0.0.1"})

    headers = build_forwarding_headers(request)

    assert REQUEST_ID_HEADER not in headers


_PEER_ADDRESS = "203.0.113.7"
_TRUSTED_PROXY_ADDRESS = "10.0.0.2"


def _make_request(
    *, trusted_proxies: list[str], peer: str, forwarded_for: str | None
) -> web.Request:
    app = web.Application()
    app[TRUSTED_PROXY_NETWORKS_KEY] = [ReadableCIDR(raw) for raw in trusted_proxies]
    transport = MagicMock()
    transport.get_extra_info.return_value = (peer, 54321)
    headers = {"X-Forwarded-For": forwarded_for} if forwarded_for is not None else {}
    return make_mocked_request("GET", "/", headers=headers, app=app, transport=transport)


class TestGetClientIp:
    def test_takes_the_first_x_forwarded_for_entry_without_trusted_proxies(self) -> None:
        request = _make_request(trusted_proxies=[], peer=_PEER_ADDRESS, forwarded_for="10.0.0.5")

        assert get_client_ip(request) == "10.0.0.5"

    def test_takes_the_peer_without_trusted_proxies_or_x_forwarded_for(self) -> None:
        request = _make_request(trusted_proxies=[], peer=_PEER_ADDRESS, forwarded_for=None)

        assert get_client_ip(request) == _PEER_ADDRESS

    def test_ignores_x_forwarded_for_from_an_untrusted_peer(self) -> None:
        request = _make_request(
            trusted_proxies=["10.0.0.0/24"], peer=_PEER_ADDRESS, forwarded_for="10.0.0.5"
        )

        assert get_client_ip(request) == _PEER_ADDRESS

    def test_takes_the_client_from_a_trusted_peer(self) -> None:
        request = _make_request(
            trusted_proxies=["10.0.0.0/24"],
            peer=_TRUSTED_PROXY_ADDRESS,
            forwarded_for=_PEER_ADDRESS,
        )

        assert get_client_ip(request) == _PEER_ADDRESS

    def test_stops_at_the_first_untrusted_hop_of_a_forged_chain(self) -> None:
        request = _make_request(
            trusted_proxies=["10.0.0.0/24"],
            peer=_TRUSTED_PROXY_ADDRESS,
            forwarded_for=f"10.0.0.5, {_PEER_ADDRESS}, 10.0.0.3",
        )

        assert get_client_ip(request) == _PEER_ADDRESS

    def test_matches_an_ipv4_mapped_peer_against_ipv4_ranges(self) -> None:
        request = _make_request(
            trusted_proxies=["10.0.0.0/24"],
            peer=f"::ffff:{_TRUSTED_PROXY_ADDRESS}",
            forwarded_for=_PEER_ADDRESS,
        )

        assert get_client_ip(request) == _PEER_ADDRESS

    def test_stops_at_an_entry_that_is_not_an_address(self) -> None:
        request = _make_request(
            trusted_proxies=["10.0.0.0/24"],
            peer=_TRUSTED_PROXY_ADDRESS,
            forwarded_for=f"{_PEER_ADDRESS}, unknown",
        )

        assert get_client_ip(request) == "unknown"

    def test_takes_the_outermost_hop_when_every_hop_is_trusted(self) -> None:
        request = _make_request(
            trusted_proxies=["10.0.0.0/24"],
            peer=_TRUSTED_PROXY_ADDRESS,
            forwarded_for="10.0.0.3",
        )

        assert get_client_ip(request) == "10.0.0.3"


class TestBuildForwardingHeaders:
    def test_keeps_the_chain_without_trusted_proxies(self) -> None:
        request = _make_request(trusted_proxies=[], peer=_PEER_ADDRESS, forwarded_for="10.0.0.5")

        headers = build_forwarding_headers(request)

        assert headers["X-Forwarded-For"] == f"10.0.0.5, {_PEER_ADDRESS}"

    def test_replaces_a_forged_chain_from_an_untrusted_peer(self) -> None:
        request = _make_request(
            trusted_proxies=["10.0.0.0/24"], peer=_PEER_ADDRESS, forwarded_for="10.0.0.5"
        )

        headers = build_forwarding_headers(request)

        assert headers["X-Forwarded-For"] == _PEER_ADDRESS

    def test_appends_a_trusted_peer_to_the_chain(self) -> None:
        request = _make_request(
            trusted_proxies=["10.0.0.0/24"],
            peer=_TRUSTED_PROXY_ADDRESS,
            forwarded_for=f"10.0.0.5, {_PEER_ADDRESS}",
        )

        headers = build_forwarding_headers(request)

        assert headers["X-Forwarded-For"] == f"{_PEER_ADDRESS}, {_TRUSTED_PROXY_ADDRESS}"
>>>>>>> 8f2af8dd6 (fix(BA-7374): trust X-Forwarded-For only from configured proxies in the webserver (#17265))
