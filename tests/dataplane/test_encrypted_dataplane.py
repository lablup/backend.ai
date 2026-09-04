"""G20-G24. What an encrypted overlay must be true about on the wire, on two real nodes.

Every other scenario asks whether traffic ARRIVES. These ask whether it arrives the way the
session was promised: inside ESP, with injected plaintext refused, and with the guarantee holding
when the firewall is disturbed underneath it. That distinction matters because every failure here
is silent -- the overlay keeps working, and only a capture says it stopped being encrypted.

They need a real pair of hosts (`BAI_DATAPLANE_NODES`) and an encrypted session, so they skip
where either is missing rather than passing vacuously.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import replace

import pytest

from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.testutils.dataplane import probe
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec

CHAIN_IN = "BAI-VXLAN-IN"
CHAIN_GUARD = "BAI-VXLAN-GUARD"
CHAIN_MARK = "BAI-VXLAN-MARK"


async def _vni_on(node: Node) -> int:
    result = await node.run(["ip", "-o", "link"], check=False)
    for line in result.stdout.splitlines():
        for token in line.split():
            name = token.rstrip(":@")
            if name.startswith("baivx"):
                return int(name.removeprefix("baivx"))
    raise AssertionError(f"no vxlan device on {node.name}: the session did not reach this node")


async def _vtep_of(node: Node) -> str:
    """The outer source address the node pinned onto its own vxlan device.

    Both `ip -d` forms are tried because neither is dependable: on three hosts running the same
    iproute2 6.1.0, one SEGFAULTS on ``show type vxlan`` and answers ``show dev <name>``, another
    does the reverse. A helper that picked one would fail on a host for reasons that have nothing
    to do with what is being tested.
    """
    vni = await _vni_on(node)
    dev = f"baivx{vni}"
    for argv in (
        ["ip", "-d", "link", "show", "dev", dev],
        ["ip", "-d", "link", "show", "type", "vxlan"],
    ):
        result = await node.run(argv, check=False)
        tokens = result.stdout.split()
        for i, token in enumerate(tokens):
            if token == "local" and i + 1 < len(tokens) and _looks_like_ipv4(tokens[i + 1]):
                return tokens[i + 1]
    raise AssertionError(
        f"could not read {dev}'s pinned local address on {node.name}: neither `ip -d link` form"
        " described it (this host's iproute2 crashes on at least one of them)"
    )


def _looks_like_ipv4(token: str) -> bool:
    parts = token.split(".")
    return len(parts) == 4 and all(p.isdigit() for p in parts)


class _Placement:
    """One kernel on each of two nodes, with everything the assertions need."""

    def __init__(
        self, node_a: Node, pid_a: str, ip_a: str, node_b: Node, pid_b: str, ip_b: str
    ) -> None:
        self.node_a, self.pid_a, self.ip_a = node_a, pid_a, ip_a
        self.node_b, self.pid_b, self.ip_b = node_b, pid_b, ip_b


async def _spread_or_skip(node_pair: tuple[Node, Node], session: str) -> _Placement:
    per_node = {n.name: await probe.overlay_endpoints(n, session) for n in node_pair}
    occupied = {name: eps for name, eps in per_node.items() if eps}
    if len(occupied) < 2:
        pytest.skip(
            "the MULTI_NODE session was not spread across both agents (kernels per node: "
            f"{ {name: len(eps) for name, eps in per_node.items()} }); nothing crosses the "
            "underlay, so there is no encryption to observe. Give the pair room for one kernel "
            "each, or set the resource group's agent_selection_strategy to roundrobin."
        )
    by_name = {n.name: n for n in node_pair}
    (name_a, eps_a), (name_b, eps_b) = list(occupied.items())
    return _Placement(by_name[name_a], *eps_a[0], by_name[name_b], *eps_b[0])


@pytest.fixture
def encrypted_spec(session_spec: SessionSpec, agent_ids: tuple[str, ...]) -> SessionSpec:
    return replace(
        session_spec,
        cluster_size=2,
        cluster_mode=ClusterModeEnum.MULTI_NODE,
        agent_list=agent_ids,
    )


class TestEncryptedUnderlay:
    async def test_g20_the_underlay_carries_esp_and_no_plaintext_vxlan(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        encrypted_spec: SessionSpec,
        node_pair: tuple[Node, Node],
    ) -> None:
        """The claim the whole feature rests on, checked where it is actually decidable.

        Reachability cannot tell the two apart: a session with its XFRM policy gone works exactly
        as well and is in clear text on the wire.
        """
        async with session_driver.session(encrypted_spec, "dp-g20") as handle:
            placed = await _spread_or_skip(node_pair, str(handle.session_id))
            if not await _is_encrypted(placed.node_a):
                pytest.skip("this session is not encrypted; there is no ESP to look for")
            iface = await probe.vtep_interface(placed.node_a, await _vtep_of(placed.node_a))

            async def cross_node_traffic() -> None:
                await probe.reaches(placed.node_a, placed.pid_a, placed.ip_b)

            seen = await probe.capture_underlay(placed.node_a, iface, cross_node_traffic)
            assert seen.is_encrypted_only, (
                f"the overlay's own frames were on the wire in clear text on {placed.node_a.name}"
                f" (ESP={seen.esp}, plaintext VXLAN={seen.plaintext}). ESP=0 with plaintext>0 means"
                " the outbound XFRM policy did not select them -- the OUTPUT mark is missing or was"
                " overwritten; both>0 means only part of the traffic is protected."
            )

    async def test_g21_clearing_the_output_mark_stops_traffic_instead_of_leaking_it(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        encrypted_spec: SessionSpec,
        node_pair: tuple[Node, Node],
    ) -> None:
        """MARK is not a terminating target, so anything later in the hook can clear it. What must
        not happen is the frame leaving anyway: the guard turns that into dropped traffic."""
        async with session_driver.session(encrypted_spec, "dp-g21") as handle:
            placed = await _spread_or_skip(node_pair, str(handle.session_id))
            node = placed.node_a
            if not await _is_encrypted(node):
                pytest.skip("this session is not encrypted; there is no mark to clear")
            iface = await probe.vtep_interface(node, await _vtep_of(node))
            mark_rules = await probe.iptables_rules(node, "mangle", CHAIN_MARK)
            marks = [rule for rule in mark_rules if rule.startswith(f"-A {CHAIN_MARK}")]
            assert marks, f"{CHAIN_MARK} on {node.name} has no rule to clear"

            for rule in marks:
                await node.run(
                    [
                        "sudo",
                        "-n",
                        "iptables",
                        "-t",
                        "mangle",
                        *rule.replace("-A", "-D", 1).split()[1:],
                    ],
                    check=False,
                )
            try:

                async def cross_node_traffic() -> None:
                    await probe.reaches(node, placed.pid_a, placed.ip_b)

                seen = await probe.capture_underlay(node, iface, cross_node_traffic)
                assert seen.plaintext == 0, (
                    f"with the OUTPUT mark gone, {seen.plaintext} VXLAN frames left"
                    f" {node.name} in clear text. The egress guard in {CHAIN_GUARD} is supposed to"
                    " drop exactly these, so the session goes visibly dead rather than quietly"
                    " unencrypted."
                )
            finally:
                for rule in marks:
                    await node.run(
                        ["sudo", "-n", "iptables", "-t", "mangle", "-A", *rule.split()[1:]],
                        check=False,
                    )


class TestFirewallOwnership:
    async def test_g22_a_displaced_jump_is_put_back_at_the_head(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        encrypted_spec: SessionSpec,
        node_pair: tuple[Node, Node],
    ) -> None:
        """A co-tenant inserting its own rule at position 1 leaves ours present but unreachable --
        which `iptables -C` cannot see. The reconcile reads the order, so it can."""
        async with session_driver.session(encrypted_spec, "dp-g22") as handle:
            placed = await _spread_or_skip(node_pair, str(handle.session_id))
            node = placed.node_a
            if not await _is_encrypted(node):
                pytest.skip("this session is not encrypted; the chains are not installed")
            assert await probe.jump_position(node, "filter", "INPUT", CHAIN_IN) == 1

            await node.run(
                [
                    "sudo",
                    "-n",
                    "iptables",
                    "-I",
                    "INPUT",
                    "1",
                    "-p",
                    "udp",
                    "--dport",
                    "1",
                    "-j",
                    "ACCEPT",
                ],
                check=False,
            )
            try:
                displaced = await probe.jump_position(node, "filter", "INPUT", CHAIN_IN)
                assert displaced == 2, (
                    "the harness could not displace the jump, so this scenario would pass without"
                    f" testing anything (position={displaced})"
                )
                restored = await _wait_for_jump_head(node)
                assert restored, (
                    f"{CHAIN_IN}'s jump stayed below another rule on {node.name}. Everything"
                    " above it decides whether our chain runs at all, so a displaced jump is an"
                    " open receive side that every presence check reports as fine."
                )
            finally:
                await node.run(
                    [
                        "sudo",
                        "-n",
                        "iptables",
                        "-D",
                        "INPUT",
                        "-p",
                        "udp",
                        "--dport",
                        "1",
                        "-j",
                        "ACCEPT",
                    ],
                    check=False,
                )

    async def test_g23_a_flushed_chain_is_refilled(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        encrypted_spec: SessionSpec,
        node_pair: tuple[Node, Node],
    ) -> None:
        """`iptables -F` between two reconciles is the case the drift check exists for: the devices
        stay up and encrypted while the receive side is wide open again."""
        async with session_driver.session(encrypted_spec, "dp-g23") as handle:
            placed = await _spread_or_skip(node_pair, str(handle.session_id))
            node = placed.node_a
            if not await _is_encrypted(node):
                pytest.skip("this session is not encrypted; the chains are not installed")
            before = await probe.iptables_rules(node, "filter", CHAIN_IN)
            assert any("--u32" in rule for rule in before)

            await node.run(["sudo", "-n", "iptables", "-F", CHAIN_IN], check=False)
            refilled = await _wait_for(lambda: _chain_has_rules(node, "filter", CHAIN_IN))
            assert refilled, (
                f"{CHAIN_IN} on {node.name} stayed empty after being flushed. The session keeps"
                " running and keeps encrypting what it sends, while accepting anyone's injected"
                " plaintext on the same VNI."
            )


async def _is_encrypted(node: Node) -> bool:
    """Whether this node programmed ESP for the session, i.e. the cluster has a key configured."""
    result = await node.run(["sudo", "-n", "ip", "xfrm", "state"], check=False)
    return "proto esp" in result.stdout


async def _chain_has_rules(node: Node, table: str, chain: str) -> bool:
    return any("--u32" in rule for rule in await probe.iptables_rules(node, table, chain))


async def _wait_for_jump_head(node: Node) -> bool:
    return await _wait_for(
        lambda: _jump_is_first(node),
    )


async def _jump_is_first(node: Node) -> bool:
    return await probe.jump_position(node, "filter", "INPUT", CHAIN_IN) == 1


async def _wait_for(
    condition: Callable[[], Awaitable[bool]], *, attempts: int = 30, delay: float = 2.0
) -> bool:
    """Poll a condition the reconcile loop restores, rather than guessing its period."""
    for _ in range(attempts):
        if await condition():
            return True
        await asyncio.sleep(delay)
    return False
