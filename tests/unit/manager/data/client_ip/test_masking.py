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
