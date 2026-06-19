"""Unit tests for ai.backend.appproxy.common.client_ip."""

from __future__ import annotations

import ipaddress
from collections.abc import Sequence
from unittest.mock import Mock

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.client_ip import ClientIPResolver, IPNetwork, IPValidator
from ai.backend.appproxy.common.errors import ClientIPNotAllowed


def _nets(*cidrs: str) -> list[IPNetwork]:
    return [ipaddress.ip_network(c) for c in cidrs]


def _make_request(remote: str | None, forwarded_for: str | None) -> web.Request:
    """Build a mocked aiohttp request with the given peer address and
    ``X-Forwarded-For`` header. ``request.remote`` derives from the transport
    peername, so a mock transport supplies it."""
    headers = {"X-Forwarded-For": forwarded_for} if forwarded_for is not None else {}
    transport = Mock()
    transport.get_extra_info.side_effect = lambda key, default=None: (
        (remote, 0) if key == "peername" and remote is not None else default
    )
    return make_mocked_request("GET", "/", headers=headers, transport=transport)


class TestIPValidator:
    @pytest.mark.parametrize(
        ("allowed", "client_ip", "expected"),
        [
            # No restriction -> every client is allowed.
            (None, "203.0.113.5", True),
            ("", "203.0.113.5", True),
            ("   ", "203.0.113.5", True),
            # Bare IP is a host route.
            ("203.0.113.5", "203.0.113.5", True),
            ("203.0.113.5", "203.0.113.6", False),
            # CIDR membership.
            ("10.0.0.0/8", "10.1.2.3", True),
            ("10.0.0.0/8", "11.0.0.1", False),
            # Multiple entries, any match allows.
            ("10.0.0.0/8, 192.168.0.0/16", "192.168.1.1", True),
            ("10.0.0.0/8, 192.168.0.0/16", "172.16.0.1", False),
            # Unparseable client IP is rejected (fail-closed).
            ("10.0.0.0/8", "not-an-ip", False),
            # IPv6.
            ("fd00::/8", "fd00::1", True),
            ("fd00::/8", "2001:db8::1", False),
        ],
    )
    def test_is_allowed(self, allowed: str | None, client_ip: str, expected: bool) -> None:
        assert IPValidator(allowed).is_allowed(client_ip) is expected

    def test_invalid_entries_are_skipped_not_raised(self) -> None:
        # A malformed entry is dropped; valid entries still enforce.
        validator = IPValidator("garbage, 10.0.0.0/8")
        assert validator.is_allowed("10.0.0.1") is True
        assert validator.is_allowed("11.0.0.1") is False

    def test_all_invalid_means_no_restriction(self) -> None:
        validator = IPValidator("garbage, also-bad")
        assert validator.is_restricted is False
        assert validator.is_allowed("203.0.113.5") is True

    def test_is_restricted(self) -> None:
        assert IPValidator(None).is_restricted is False
        assert IPValidator("10.0.0.0/8").is_restricted is True

    def test_ranges_normalizes_entries(self) -> None:
        # Bare IPs become host routes; whitespace stripped; order preserved.
        validator = IPValidator(" 10.0.0.0/8 , 203.0.113.5 ")
        assert validator.ranges == ["10.0.0.0/8", "203.0.113.5/32"]

    def test_ranges_empty_when_unrestricted(self) -> None:
        assert IPValidator(None).ranges == []


class TestClientIPResolver:
    @pytest.mark.parametrize(
        ("peer", "forwarded_for", "trusted", "expected"),
        [
            # No X-Forwarded-For header -> always the direct peer, regardless of trust.
            ("203.0.113.5", None, ("10.0.0.0/8",), "203.0.113.5"),
            # Empty header string is treated the same as no header.
            ("203.0.113.5", "", ("10.0.0.0/8",), "203.0.113.5"),
            # Peer is not a trusted proxy -> ignore the (forgeable) header, use peer.
            ("203.0.113.5", "1.2.3.4", ("10.0.0.0/8",), "203.0.113.5"),
            # No trusted proxies configured -> nothing is trusted -> use peer.
            ("10.0.0.9", "1.2.3.4", (), "10.0.0.9"),
            # Peer trusted, single forwarded entry -> that entry is the client.
            ("10.0.0.9", "203.0.113.5", ("10.0.0.0/8",), "203.0.113.5"),
            # Peer trusted, chain of trusted proxies on the right are skipped,
            # first untrusted (from the right) wins.
            (
                "10.0.0.9",
                "203.0.113.5, 10.1.1.1, 10.2.2.2",
                ("10.0.0.0/8",),
                "203.0.113.5",
            ),
            # An untrusted hop to the left of a trusted one is not selected;
            # only the nearest untrusted (rightmost) is.
            (
                "10.0.0.9",
                "9.9.9.9, 203.0.113.5, 10.1.1.1",
                ("10.0.0.0/8",),
                "203.0.113.5",
            ),
            # Every hop is a trusted proxy -> fall back to the leftmost (claimed origin).
            ("10.0.0.9", "10.1.1.1, 10.2.2.2", ("10.0.0.0/8",), "10.1.1.1"),
            # Whitespace around entries is stripped.
            ("10.0.0.9", "  203.0.113.5 , 10.1.1.1 ", ("10.0.0.0/8",), "203.0.113.5"),
            # Header with no usable entries (only separators) -> fall back to peer.
            ("10.0.0.9", " , ", ("10.0.0.0/8",), "10.0.0.9"),
            # Multiple trusted networks are all honored.
            (
                "192.168.1.1",
                "203.0.113.5, 172.16.0.1",
                ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"),
                "203.0.113.5",
            ),
            # IPv6 peer + forwarded client.
            ("fd00::1", "2001:db8::5", ("fd00::/8",), "2001:db8::5"),
        ],
        ids=[
            "no-header",
            "empty-header",
            "peer-untrusted-ignores-header",
            "no-trusted-proxies",
            "single-forwarded-entry",
            "skip-trailing-trusted-proxies",
            "nearest-untrusted-wins",
            "all-hops-trusted-uses-leftmost",
            "strips-whitespace",
            "empty-chain-falls-back-to-peer",
            "multiple-trusted-networks",
            "ipv6",
        ],
    )
    def test_resolve(
        self,
        peer: str,
        forwarded_for: str | None,
        trusted: tuple[str, ...],
        expected: str,
    ) -> None:
        trusted_networks: Sequence[IPNetwork] = _nets(*trusted)
        request = _make_request(peer, forwarded_for)
        assert ClientIPResolver(trusted_networks).resolve(request) == expected

    def test_missing_peer_raises(self) -> None:
        request = _make_request(None, None)
        with pytest.raises(ClientIPNotAllowed):
            ClientIPResolver(_nets("10.0.0.0/8")).resolve(request)
