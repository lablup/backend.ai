"""Unit tests for ai.backend.appproxy.common.client_ip.

X-Forwarded-For resolution is no longer done here — the worker installs
``aiohttp_remotes.XForwardedStrict`` as a middleware, so ``request.remote`` is
already the real client IP. Only the per-circuit allowlist matcher lives in this
module and is unit-tested below.
"""

from __future__ import annotations

import pytest

from ai.backend.appproxy.common.client_ip import ClientIPValidator


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
        assert ClientIPValidator(allowed).is_allowed(client_ip) is expected

    def test_invalid_entries_are_skipped_not_raised(self) -> None:
        # A malformed entry is dropped; valid entries still enforce.
        validator = ClientIPValidator("garbage, 10.0.0.0/8")
        assert validator.is_allowed("10.0.0.1") is True
        assert validator.is_allowed("11.0.0.1") is False

    def test_all_invalid_means_no_restriction(self) -> None:
        validator = ClientIPValidator("garbage, also-bad")
        assert validator.is_restricted is False
        assert validator.is_allowed("203.0.113.5") is True

    def test_is_restricted(self) -> None:
        assert ClientIPValidator(None).is_restricted is False
        assert ClientIPValidator("10.0.0.0/8").is_restricted is True

    def test_ranges_normalizes_entries(self) -> None:
        # Bare IPs become host routes; whitespace stripped; order preserved.
        validator = ClientIPValidator(" 10.0.0.0/8 , 203.0.113.5 ")
        assert validator.ranges == ["10.0.0.0/8", "203.0.113.5/32"]

    def test_ranges_empty_when_unrestricted(self) -> None:
        assert ClientIPValidator(None).ranges == []
