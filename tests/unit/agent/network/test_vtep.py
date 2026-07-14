"""Unit tests for the VTEP validation shared by the agent and the network helper (BEP-1062).

The VTEP is the address every peer programs into its FDB. Publishing one this node cannot be
reached at does not fail — it builds an overlay that comes up, logs nothing and carries no traffic
— so what this module rejects is the whole point of it.
"""

from __future__ import annotations

import socket
from typing import Any

import psutil
import pytest

from ai.backend.agent.network.vtep import uplink_for_ip, usable_vtep


class _Addr:
    def __init__(self, address: str, family: int = socket.AF_INET) -> None:
        self.family = family
        self.address = address


class _Stats:
    def __init__(self, isup: bool) -> None:
        self.isup = isup


@pytest.fixture
def host(monkeypatch: pytest.MonkeyPatch) -> Any:
    """A host holding 10.0.0.5 on an UP bond0, and 10.9.9.9 on a DOWN eth1.

    Deliberately NOT eth0, so a result of "eth0" can only be the fallback.
    """

    def net_if_addrs() -> dict[str, list[_Addr]]:
        return {
            "lo": [_Addr("127.0.0.1")],
            "bond0": [_Addr("10.0.0.5"), _Addr("fe80::1", socket.AF_INET6)],
            "eth1": [_Addr("10.9.9.9")],
        }

    def net_if_stats() -> dict[str, _Stats]:
        return {"lo": _Stats(True), "bond0": _Stats(True), "eth1": _Stats(False)}

    monkeypatch.setattr(psutil, "net_if_addrs", net_if_addrs)
    monkeypatch.setattr(psutil, "net_if_stats", net_if_stats)


class TestUsableVtep:
    def test_an_address_this_host_holds_on_a_live_interface_passes(self, host: Any) -> None:
        assert usable_vtep("10.0.0.5") == "10.0.0.5"

    @pytest.mark.parametrize(
        ("host_ip", "why"),
        [
            ("", "the bind-host default: not an address at all"),
            ("0.0.0.0", "the other default: accepted by iproute2, points nowhere"),
            ("127.0.0.1", "loopback reaches no peer"),
            ("169.254.10.1", "link-local: what a host holds when DHCP failed"),
            ("224.0.0.1", "multicast is not a tunnel endpoint"),
            ("10.0.0.6", "a routable address this host does not hold (stale config)"),
            ("10.9.9.9", "held, but by an interface that is DOWN"),
            ("agent-1.example.com", "an FQDN is not an FDB destination"),
            ("fd00::1", "the vxlan path is IPv4-only end to end"),
        ],
    )
    def test_an_unusable_address_yields_none(self, host: Any, host_ip: str, why: str) -> None:
        assert usable_vtep(host_ip) is None, why


class TestUplinkForIp:
    def test_the_vxlan_device_rides_the_interface_carrying_the_vtep(self, host: Any) -> None:
        assert uplink_for_ip("10.0.0.5") == "bond0"

    def test_a_down_interface_is_not_an_uplink(self, host: Any) -> None:
        # Building the vxlan device on a down interface would come up happily and carry nothing.
        assert uplink_for_ip("10.9.9.9") == "eth0"  # the fallback, not the down eth1

    def test_an_unheld_address_falls_back(self, host: Any) -> None:
        assert uplink_for_ip("10.0.0.6") == "eth0"
