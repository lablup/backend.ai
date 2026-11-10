from __future__ import annotations

import pytest

from ai.backend.manager.data.client_ip.masking import ClientIPMasker, ClientIPMaskingMode


@pytest.mark.parametrize(
    ("client_ip", "expected"),
    [
        ("203.0.113.7", "203.0.113.7"),
        ("2001:db8:1:2::1", "2001:db8:1:2::1"),
        ("2001:0db8:0001:0002:0000:0000:0000:0001", "2001:db8:1:2::1"),
    ],
)
def test_no_masking_keeps_the_address(client_ip: str, expected: str) -> None:
    masker = ClientIPMasker(ClientIPMaskingMode.NONE)

    assert masker.mask(client_ip) == expected


@pytest.mark.parametrize(
    ("client_ip", "expected"),
    [
        ("203.0.113.7", "203.0.113.0"),
        ("10.1.2.34", "10.1.2.0"),
        ("2001:db8:1:2::1", "2001:db8:1::"),
        ("::1", "::"),
    ],
)
def test_truncation_zeroes_the_host_bits(client_ip: str, expected: str) -> None:
    masker = ClientIPMasker(ClientIPMaskingMode.TRUNCATE)

    assert masker.mask(client_ip) == expected


@pytest.mark.parametrize("mode", list(ClientIPMaskingMode))
def test_a_missing_address_stays_missing(mode: ClientIPMaskingMode) -> None:
    assert ClientIPMasker(mode).mask(None) is None


@pytest.mark.parametrize("mode", list(ClientIPMaskingMode))
@pytest.mark.parametrize(
    "client_ip",
    [
        "not-an-address",
        "203.0.113.7, 10.0.0.1",
        "203.0.113.7:8080",
        "",
        "10.1.2.0/24",
    ],
)
def test_an_unusable_address_is_dropped(mode: ClientIPMaskingMode, client_ip: str) -> None:
    """A forged X-Forwarded-For must not reach the INET column and break the write."""
    assert ClientIPMasker(mode).mask(client_ip) is None


@pytest.mark.parametrize("client_ip", ["203.0.113.7", "2001:db8:1:2::1"])
def test_dropping_records_no_address(client_ip: str) -> None:
    """A deployment that must keep no address at all has a mode for it."""
    assert ClientIPMasker(ClientIPMaskingMode.DROP).mask(client_ip) is None


@pytest.mark.parametrize(
    ("client_ip", "ipv4_prefix", "expected"),
    [
        ("203.0.113.7", 24, "203.0.113.0"),
        ("203.0.113.7", 16, "203.0.0.0"),
        ("203.0.113.7", 8, "203.0.0.0"),
        ("203.0.113.7", 0, "0.0.0.0"),
        ("203.0.113.7", 32, "203.0.113.7"),
    ],
)
def test_the_ipv4_width_is_what_the_policy_says(
    client_ip: str, ipv4_prefix: int, expected: str
) -> None:
    """How deep an address must be cut to count as anonymous differs by jurisdiction."""
    masker = ClientIPMasker(ClientIPMaskingMode.TRUNCATE, ipv4_prefix=ipv4_prefix)

    assert masker.mask(client_ip) == expected


@pytest.mark.parametrize(
    ("client_ip", "ipv6_prefix", "expected"),
    [
        ("2001:db8:1:2::1", 48, "2001:db8:1::"),
        ("2001:db8:1:2::1", 32, "2001:db8::"),
        ("2001:db8:1:2::1", 64, "2001:db8:1:2::"),
    ],
)
def test_the_ipv6_width_is_what_the_policy_says(
    client_ip: str, ipv6_prefix: int, expected: str
) -> None:
    """An ISP handing out a /48 whole makes /48 masking no anonymisation at all."""
    masker = ClientIPMasker(ClientIPMaskingMode.TRUNCATE, ipv6_prefix=ipv6_prefix)

    assert masker.mask(client_ip) == expected


def test_the_built_in_widths_are_the_google_ones() -> None:
    masker = ClientIPMasker(ClientIPMaskingMode.TRUNCATE)

    assert (masker.ipv4_prefix, masker.ipv6_prefix) == (24, 48)


@pytest.mark.parametrize("mode", [ClientIPMaskingMode.NONE, ClientIPMaskingMode.DROP])
def test_the_widths_are_ignored_outside_truncation(mode: ClientIPMaskingMode) -> None:
    masker = ClientIPMasker(mode, ipv4_prefix=8, ipv6_prefix=16)
    plain = ClientIPMasker(mode)

    assert masker.mask("203.0.113.7") == plain.mask("203.0.113.7")
