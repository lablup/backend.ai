"""The underlay measurement the overlay-MTU guard rests on.

Each shape below is the real output of the CNI named in its comment, captured on a two-node
cluster (see the module docstring of path_mtu.py for the measured numbers).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import pytest

from ai.backend.agent.network.path_mtu import parse_route_mtus, underlay_mtu

# Captured verbatim from `ip -4 route show default dev eth0` inside a pod on each CNI.
# cilium in tunnel mode: the device stays at 1500 and the ceiling is on the route.
_CILIUM_TUNNEL_ROUTE = "default via 10.250.0.222 mtu 1450 \n"
# cilium in native-routing mode: the route names an MTU too, but the full one.
_CILIUM_NATIVE_ROUTE = "default via 10.250.0.222 mtu 1500 \n"
# flannel: nothing on the route; the device MTU is what was lowered.
_FLANNEL_ROUTE = "default via 10.250.0.1 \n"
# calico: same, via its link-local next hop.
_CALICO_ROUTE = "default via 169.254.1.1 \n"


class TestParseRouteMtus:
    def test_reads_every_mtu_attribute(self) -> None:
        assert parse_route_mtus(_CILIUM_TUNNEL_ROUTE) == [1450]
        assert parse_route_mtus(_CILIUM_TUNNEL_ROUTE + _CILIUM_NATIVE_ROUTE) == [1450, 1500]

    def test_route_without_mtu_contributes_nothing(self) -> None:
        # Not a 1500 default: a route with no `mtu` imposes no ceiling of its own, and inventing
        # one would mask a device MTU that is genuinely smaller.
        assert parse_route_mtus(_FLANNEL_ROUTE) == []
        assert parse_route_mtus(_CALICO_ROUTE) == []

    def test_ignores_unrelated_numbers(self) -> None:
        assert parse_route_mtus("default via 10.0.0.1 dev eth0 metric 600 \n") == []


def _readers(
    route_output: str, dev_mtu: int | None
) -> tuple[Callable[[list[str]], Awaitable[str]], Callable[[str], Awaitable[int | None]]]:
    async def read_command(argv: list[str]) -> str:
        return route_output

    async def read_dev_mtu(dev: str) -> int | None:
        return dev_mtu

    return read_command, read_dev_mtu


class TestUnderlayMtu:
    @pytest.mark.parametrize(
        ("label", "route", "dev_mtu", "expected"),
        [
            # The device is honest; nothing on the route. Each (device MTU, expected) pair is
            # the underlay a DF sweep actually found on that CNI (max payload + 78).
            ("flannel-host-gw", _FLANNEL_ROUTE, 1500, 1500),
            ("flannel-vxlan", _FLANNEL_ROUTE, 1450, 1450),
            ("flannel-ipip", _FLANNEL_ROUTE, 1480, 1480),
            ("flannel-wireguard", _FLANNEL_ROUTE, 1420, 1420),
            ("calico-ipip", _CALICO_ROUTE, 1480, 1480),
            ("calico-vxlan", _CALICO_ROUTE, 1450, 1450),
            ("calico-no-encap", _CALICO_ROUTE, 1500, 1500),
            # The device lies at 1500 and only the route tells the truth. This is the case a
            # device-only reading gets wrong by exactly the 50 bytes that black-hole traffic.
            ("cilium-vxlan", _CILIUM_TUNNEL_ROUTE, 1500, 1450),
            ("cilium-native", _CILIUM_NATIVE_ROUTE, 1500, 1500),
        ],
    )
    async def test_matches_measured_cni_behaviour(
        self, label: str, route: str, dev_mtu: int, expected: int
    ) -> None:
        read_command, read_dev_mtu = _readers(route, dev_mtu)
        assert (
            await underlay_mtu("eth0", read_command=read_command, read_dev_mtu=read_dev_mtu)
        ) == expected, label

    async def test_unmeasurable_is_none_not_a_guess(self) -> None:
        # Reporting a guess here would refuse every session on a node we simply could not read.
        async def failing_command(argv: list[str]) -> str:
            raise RuntimeError("no iproute2")

        async def no_dev(dev: str) -> int | None:
            return None

        assert (
            await underlay_mtu("eth0", read_command=failing_command, read_dev_mtu=no_dev)
        ) is None

    async def test_route_failure_still_yields_the_device_mtu(self) -> None:
        async def failing_command(argv: list[str]) -> str:
            raise RuntimeError("no iproute2")

        async def dev(dev_name: str) -> int | None:
            return 1450

        assert (await underlay_mtu("eth0", read_command=failing_command, read_dev_mtu=dev)) == 1450

    async def test_peer_ip_selects_a_per_destination_query(self) -> None:
        seen: list[list[str]] = []

        async def read_command(argv: list[str]) -> str:
            seen.append(argv)
            return _FLANNEL_ROUTE

        async def dev(dev_name: str) -> int | None:
            return 1500

        await underlay_mtu("eth0", peer_ip="10.0.0.2", read_command=read_command, read_dev_mtu=dev)
        assert seen == [["ip", "-4", "route", "get", "10.0.0.2"]]
