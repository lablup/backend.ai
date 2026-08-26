from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from dateutil.tz import tzutc

from ai.backend.common.exception import InvalidIpAddressValue
from ai.backend.manager.api.rest.middleware import auth as auth_module
from ai.backend.manager.api.rest.middleware.auth import (
    FORWARDED_PREFIX_HEADER,
    FORWARDED_URL_HEADER,
    TRUSTED_PROXY_NETWORKS_KEY,
    extract_client_ip,
    is_from_trusted_proxy,
    parse_trusted_proxy_networks,
    sign_request,
)

SIGN_METHOD = "HMAC-SHA256"
SECRET_KEY = "fake-secret-key"
DEFAULT_HOST = "10.214.150.180:8081"
DEFAULT_PATH = "/admin/gql"
FORWARDED_URL = "https://example.invalid/proxied/admin/gql"
FORWARDED_PREFIX = "/bai"
TRUSTED_PROXY = "10.0.0.1"
UNTRUSTED_PEER = "203.0.113.7"


def _make_request(
    *,
    host: str = DEFAULT_HOST,
    raw_path: str = DEFAULT_PATH,
    forwarded_url: str | None = None,
    forwarded_prefix: str | None = None,
    forwarded_for: str | None = None,
    peer: str | None = TRUSTED_PROXY,
    trusted_proxies: list[str] | None = None,
) -> web.Request:
    date = datetime(2026, 8, 10, 3, 4, 5, tzinfo=tzutc())
    state: dict[str, Any] = {"date": date, "raw_date": date.isoformat()}
    headers = {"X-BackendAI-Version": "v8.20240915"}
    if forwarded_url is not None:
        headers[FORWARDED_URL_HEADER] = forwarded_url
    if forwarded_prefix is not None:
        headers[FORWARDED_PREFIX_HEADER] = forwarded_prefix
    if forwarded_for is not None:
        headers["X-Forwarded-For"] = forwarded_for

    request = MagicMock(spec=web.Request)
    request.__getitem__.side_effect = state.__getitem__
    request.headers = headers
    request.remote = peer
    request.method = "POST"
    request.host = host
    request.raw_path = raw_path
    request.content_type = "application/json"
    request.can_read_body = False
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


@pytest.fixture(autouse=True)
def reset_deprecation_warning() -> None:
    auth_module._warn_forwarded_url_without_trusted_proxies.cache_clear()
    auth_module._warn_forwarded_url_path_deprecated.cache_clear()


def test_parse_trusted_proxy_networks_accepts_bare_addresses_cidrs_and_wildcards() -> None:
    networks = parse_trusted_proxy_networks(["10.0.0.1", "172.16.0.0/12", "10.1.*.*", "fd00::/8"])

    assert [str(network) for network in networks] == [
        "10.0.0.1/32",
        "172.16.0.0/12",
        "10.1.0.0/16",
        "fd00::/8",
    ]


def test_parse_trusted_proxy_networks_rejects_invalid_value() -> None:
    with pytest.raises(InvalidIpAddressValue):
        parse_trusted_proxy_networks(["not-an-address"])


def test_is_from_trusted_proxy_without_configuration() -> None:
    request = _make_request(peer=TRUSTED_PROXY, trusted_proxies=[])

    assert not is_from_trusted_proxy(request)


def test_is_from_trusted_proxy_with_matching_peer() -> None:
    request = _make_request(peer="10.1.2.3", trusted_proxies=["10.0.0.0/8"])

    assert is_from_trusted_proxy(request)


def test_is_from_trusted_proxy_with_unmatched_peer() -> None:
    request = _make_request(peer=UNTRUSTED_PEER, trusted_proxies=["10.0.0.0/8"])

    assert not is_from_trusted_proxy(request)


def test_is_from_trusted_proxy_without_transport() -> None:
    request = _make_request(peer=None, trusted_proxies=["10.0.0.0/8"])

    assert not is_from_trusted_proxy(request)


async def test_forwarded_url_is_ignored_from_untrusted_peer() -> None:
    forwarded = _make_request(
        forwarded_url=FORWARDED_URL,
        peer=UNTRUSTED_PEER,
        trusted_proxies=["10.0.0.0/8"],
    )
    plain = _make_request(peer=UNTRUSTED_PEER, trusted_proxies=["10.0.0.0/8"])

    assert await sign_request(SIGN_METHOD, forwarded, SECRET_KEY) == await sign_request(
        SIGN_METHOD, plain, SECRET_KEY
    )


async def test_forwarded_url_is_honored_from_trusted_peer() -> None:
    forwarded = _make_request(
        forwarded_url=FORWARDED_URL,
        peer=TRUSTED_PROXY,
        trusted_proxies=["10.0.0.0/8"],
    )
    upstream = _make_request(
        host="example.invalid",
        raw_path="/proxied/admin/gql",
        peer=TRUSTED_PROXY,
        trusted_proxies=["10.0.0.0/8"],
    )

    assert await sign_request(SIGN_METHOD, forwarded, SECRET_KEY) == await sign_request(
        SIGN_METHOD, upstream, SECRET_KEY
    )


async def test_forwarded_url_is_honored_without_trusted_proxies_configured() -> None:
    forwarded = _make_request(
        forwarded_url=FORWARDED_URL,
        peer=UNTRUSTED_PEER,
        trusted_proxies=[],
    )
    upstream = _make_request(
        host="example.invalid",
        raw_path="/proxied/admin/gql",
        peer=UNTRUSTED_PEER,
        trusted_proxies=[],
    )

    assert await sign_request(SIGN_METHOD, forwarded, SECRET_KEY) == await sign_request(
        SIGN_METHOD, upstream, SECRET_KEY
    )


async def test_deprecation_warning_is_logged_once_without_trusted_proxies(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("WARNING", logger=auth_module.__spec__.name):
        for _ in range(2):
            await sign_request(
                SIGN_METHOD,
                _make_request(forwarded_url=FORWARDED_URL, trusted_proxies=[]),
                SECRET_KEY,
            )

    warnings = [
        record for record in caplog.records if "manager.trusted-proxies" in record.getMessage()
    ]
    assert len(warnings) == 1


async def test_no_warning_when_forwarded_url_is_absent(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("WARNING", logger=auth_module.__spec__.name):
        await sign_request(SIGN_METHOD, _make_request(trusted_proxies=[]), SECRET_KEY)

    assert not [
        record for record in caplog.records if "manager.trusted-proxies" in record.getMessage()
    ]


class TestSignRequestForwardedPrefix:
    @pytest.mark.parametrize(
        ("peer", "expected_path"),
        [
            pytest.param(
                TRUSTED_PROXY, FORWARDED_PREFIX + DEFAULT_PATH, id="honored_from_trusted_peer"
            ),
            pytest.param(UNTRUSTED_PEER, DEFAULT_PATH, id="ignored_from_untrusted_peer"),
        ],
    )
    async def test_is_honored_based_on_trust(self, peer: str, expected_path: str) -> None:
        prefixed = _make_request(
            forwarded_prefix=FORWARDED_PREFIX, peer=peer, trusted_proxies=["10.0.0.0/8"]
        )
        literal = _make_request(raw_path=expected_path, peer=peer, trusted_proxies=["10.0.0.0/8"])

        assert await sign_request(SIGN_METHOD, prefixed, SECRET_KEY) == await sign_request(
            SIGN_METHOD, literal, SECRET_KEY
        )

    @pytest.mark.parametrize(
        ("raw_prefix", "expected_path"),
        [
            pytest.param(
                FORWARDED_PREFIX + "/",
                FORWARDED_PREFIX + DEFAULT_PATH,
                id="trailing_slash_stripped",
            ),
            pytest.param("", DEFAULT_PATH, id="empty_prefix_is_no_prefix"),
        ],
    )
    async def test_normalizes_prefix_value(self, raw_prefix: str, expected_path: str) -> None:
        given = _make_request(
            forwarded_prefix=raw_prefix, peer=TRUSTED_PROXY, trusted_proxies=["10.0.0.0/8"]
        )
        literal = _make_request(
            raw_path=expected_path, peer=TRUSTED_PROXY, trusted_proxies=["10.0.0.0/8"]
        )

        assert await sign_request(SIGN_METHOD, given, SECRET_KEY) == await sign_request(
            SIGN_METHOD, literal, SECRET_KEY
        )

    async def test_takes_priority_over_forwarded_url_path(self) -> None:
        both = _make_request(
            forwarded_prefix=FORWARDED_PREFIX,
            forwarded_url=FORWARDED_URL,
            peer=TRUSTED_PROXY,
            trusted_proxies=["10.0.0.0/8"],
        )
        upstream_host_with_prefixed_path = _make_request(
            host="example.invalid",
            raw_path=FORWARDED_PREFIX + DEFAULT_PATH,
            peer=TRUSTED_PROXY,
            trusted_proxies=["10.0.0.0/8"],
        )

        assert await sign_request(SIGN_METHOD, both, SECRET_KEY) == await sign_request(
            SIGN_METHOD, upstream_host_with_prefixed_path, SECRET_KEY
        )


class TestExtractClientIP:
    """Client IP resolution over the X-Forwarded-For chain."""

    def test_single_proxy_hop(self) -> None:
        request = _make_request(
            forwarded_for="203.0.113.9",
            peer="10.0.0.1",
            trusted_proxies=["10.0.0.0/8"],
        )

        assert extract_client_ip(request) == "203.0.113.9"

    def test_multiple_trusted_hops(self) -> None:
        request = _make_request(
            forwarded_for="203.0.113.9, 10.0.0.5, 10.0.0.6",
            peer="10.0.0.1",
            trusted_proxies=["10.0.0.0/8"],
        )

        assert extract_client_ip(request) == "203.0.113.9"

    def test_no_forwarded_for_falls_back_to_peer(self) -> None:
        request = _make_request(peer="10.0.0.1", trusted_proxies=["10.0.0.0/8"])

        assert extract_client_ip(request) == "10.0.0.1"

    def test_forged_header_from_untrusted_peer_is_ignored(self) -> None:
        request = _make_request(
            forwarded_for="1.2.3.4",
            peer=UNTRUSTED_PEER,
            trusted_proxies=["10.0.0.0/8"],
        )

        assert extract_client_ip(request) == UNTRUSTED_PEER

    def test_untrusted_hop_between_trusted_ones_wins(self) -> None:
        request = _make_request(
            forwarded_for="203.0.113.9, 198.51.100.4, 10.0.0.5",
            peer="10.0.0.1",
            trusted_proxies=["10.0.0.0/8"],
        )

        assert extract_client_ip(request) == "198.51.100.4"

    def test_every_hop_trusted_returns_the_outermost(self) -> None:
        request = _make_request(
            forwarded_for="10.0.0.9, 10.0.0.5",
            peer="10.0.0.1",
            trusted_proxies=["10.0.0.0/8"],
        )

        assert extract_client_ip(request) == "10.0.0.9"

    def test_without_trusted_proxies_takes_the_first_entry(self) -> None:
        request = _make_request(
            forwarded_for="203.0.113.9, 10.0.0.5",
            peer="10.0.0.1",
            trusted_proxies=[],
        )

        assert extract_client_ip(request) == "203.0.113.9"

    def test_without_trusted_proxies_falls_back_to_remote(self) -> None:
        request = _make_request(peer="10.0.0.1", trusted_proxies=[])

        assert extract_client_ip(request) == "10.0.0.1"
