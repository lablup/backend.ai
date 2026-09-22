"""N-group. What a session's OTHER nodes see when one of its nodes fails.

Every restart scenario so far looked from the node that restarted. These look from the node that
did not: its peer's agent restarts (G1), its peer vanishes for a while and returns (G2, lite), and
the session is given up on while the peer is gone (the case an operator actually meets).

The peer "vanishes" by dropping every packet between it and the rest of the rig except the
harness's own ssh. To the manager that is a lost heartbeat; to the surviving node it is a VTEP that
stopped answering -- the same two facts a node that lost power presents, without a reboot that
would need a hand on the console to bring the privileged helper back.

Gated on the per-node restart controls, like the rolling-update scenario.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import replace
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.network.keys import member_key
from ai.backend.testutils.dataplane import probe
from ai.backend.testutils.dataplane.agent_control import AgentController
from ai.backend.testutils.dataplane.collectors.etcd_keys import flatten
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.privnet_control import PrivnetController
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec

#: The manager's heartbeat timeout is 40s by default; the lost checker runs on its own interval.
LOST_LIMIT_SEC = 90.0
#: How long the peer stays gone. Long enough for the manager to give up on it and for every
#: periodic pass on the surviving node to have run several times.
ABSENCE_SEC = 75.0
RETURN_LIMIT_SEC = 60.0
RELEASE_LIMIT_SEC = 180.0


async def _until(
    check: Callable[[], Awaitable[bool]], *, limit: float, interval: float = 2.0
) -> float | None:
    """Seconds until `check` held, or None if it did not within `limit`."""
    started = time.monotonic()
    while time.monotonic() - started < limit:
        if await check():
            return time.monotonic() - started
        await asyncio.sleep(interval)
    return (time.monotonic() - started) if await check() else None


class _Vanished:
    """Drop everything between `node` and `others`, except the harness's ssh from `home`.

    The ssh ACCEPTs go in first and sit at the top; each DROP is then inserted at position 2, under
    them. The other order cut the harness's own connection with the first DROP and left the node
    half-isolated with nothing able to reach it to undo the rest -- which is exactly the failure
    an isolation helper must be built not to have.
    """

    def __init__(self, node: Node, home: str, others: Sequence[str]) -> None:
        self._node, self._home, self._others = node, home, list(others)
        self._applied: list[list[str]] = []

    async def _add(self, rule: list[str]) -> None:
        await self._node.run(["iptables", *rule])
        self._applied.append(rule)

    async def __aenter__(self) -> None:
        try:
            await self._add([
                "-I",
                "INPUT",
                "1",
                "-s",
                self._home,
                "-p",
                "tcp",
                "--dport",
                "22",
                "-j",
                "ACCEPT",
            ])
            await self._add([
                "-I",
                "OUTPUT",
                "1",
                "-d",
                self._home,
                "-p",
                "tcp",
                "--sport",
                "22",
                "-j",
                "ACCEPT",
            ])
            for other in self._others:
                await self._add(["-I", "INPUT", "2", "-s", other, "-j", "DROP"])
                await self._add(["-I", "OUTPUT", "2", "-d", other, "-j", "DROP"])
        except BaseException:
            await self._undo()
            raise

    async def __aexit__(self, *_: object) -> None:
        await self._undo()

    async def _undo(self) -> None:
        # Reverse order, DROPs first, so the ssh ACCEPTs are the last to go; each removal names the
        # rule without its position, which `-D` takes as a match on the rule itself.
        for rule in reversed(self._applied):
            spec = [t for i, t in enumerate(rule) if not (i == 2 and t.isdigit())]
            await self._node.run(["iptables", "-D", *spec[1:]], check=False)
        self._applied.clear()


async def _session_keys(etcd: AsyncEtcd, session_id: UUID) -> dict[str, str]:
    prefix = f"network/session/{session_id}/"
    return flatten(prefix, await etcd.get_prefix(prefix) or {})


async def _sa_count(node: Node) -> int:
    result = await node.run(["ip", "xfrm", "state"], check=False)
    return sum(1 for line in result.stdout.splitlines() if line.startswith("src "))


class TestAPeerFails:
    @pytest.fixture
    def overlay_ab(self, session_spec: SessionSpec, agent_ids: tuple[str, ...]) -> SessionSpec:
        """Across the first node and the LAST: the last is the one made to vanish, and the first
        hosts the manager, so cutting the last from the first cuts it from the control plane too."""
        if len(agent_ids) < 2:
            pytest.skip("needs two nodes: a survivor and the one that fails")
        return replace(
            session_spec,
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            agent_list=(agent_ids[0], agent_ids[-1]),
        )

    @pytest.fixture
    def overlay_bystander(
        self, session_spec: SessionSpec, agent_ids: tuple[str, ...]
    ) -> SessionSpec | None:
        """A session across the two nodes NOT involved in the failure, or None on a rig with only
        the two. The bystander check is the one that says the rest of the cluster is untouched."""
        if len(agent_ids) < 3:
            return None
        return replace(
            session_spec,
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            agent_list=(agent_ids[0], agent_ids[1]),
        )

    async def test_n1_a_peers_agent_restart_leaves_this_nodes_view_of_it_intact(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        overlay_ab: SessionSpec,
        agent_ids: tuple[str, ...],
        nodes: Sequence[Node],
        node_controls: Sequence[tuple[AgentController, PrivnetController]],
        etcd: AsyncEtcd,
    ) -> None:
        """G1. The restarting node re-publishes its member record on resume; a record rewritten to
        `vtep_ip: null` was what took the peer's FDB entry out from under a healthy session."""
        survivor, peer = nodes[0], nodes[-1]
        peer_agent, _ = node_controls[-1]
        async with session_driver.session(overlay_ab, "dp-n1") as running:
            (pid_a, _ip_a), *_ = await probe.overlay_endpoints(survivor, running)
            (pid_b, ip_b), *_ = await probe.overlay_endpoints(peer, running)
            mac_b = await probe.interface_mac(peer, pid_b)
            assert await probe.fdb_has_remote(survivor, mac_b), (
                "the survivor never learned its peer"
            )
            assert await probe.reaches(survivor, pid_a, ip_b)
            record_before = await etcd.get(member_key(str(running.session_id), agent_ids[-1]))

            await peer_agent.restart()

            record_after = await etcd.get(member_key(str(running.session_id), agent_ids[-1]))
            assert record_after is not None and '"vtep_ip": null' not in record_after, (
                f"the peer's member record was rewritten by its restart: {record_after!r}"
                f" (was {record_before!r})"
            )
            assert await probe.fdb_has_remote(survivor, mac_b), (
                "the survivor's FDB lost the peer's MAC across the peer's agent restart"
            )
            delivered = await probe.delivery_ratio(
                survivor, pid_a, ip_b, count=40, payload=1200, interval=0.05
            )
            assert delivered >= 0.95, f"only {delivered:.2f} delivered after the peer's restart"

    async def test_n2_a_peer_that_vanishes_and_returns_costs_the_session_only_the_absence(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        overlay_ab: SessionSpec,
        overlay_bystander: SessionSpec | None,
        agent_ids: tuple[str, ...],
        nodes: Sequence[Node],
        node_addresses: Sequence[str],
        agent_status: Callable[[str], Awaitable[str]],
    ) -> None:
        """G2, without the reboot. While the peer is gone the survivor keeps everything it holds
        for the session -- tearing it down on a silence would turn every network blip into a
        dead session -- and the rest of the rig is untouched. When the peer is back, so is the
        session, on its own."""
        survivor, peer = nodes[0], nodes[-1]
        peer_id = agent_ids[-1]
        home, others = node_addresses[0], [a for a in node_addresses[:-1]]
        async with session_driver.session(overlay_ab, "dp-n2") as running:
            (pid_a, _ip_a), *_ = await probe.overlay_endpoints(survivor, running)
            (pid_b, ip_b), *_ = await probe.overlay_endpoints(peer, running)
            mac_b = await probe.interface_mac(peer, pid_b)
            assert await probe.reaches(survivor, pid_a, ip_b)
            sas_before = await _sa_count(survivor)

            async with _Vanished(peer, home, others):
                lost_after = await _until(
                    lambda: _status_is(agent_status, peer_id, "LOST"), limit=LOST_LIMIT_SEC
                )
                assert lost_after is not None, (
                    f"the manager still believed {peer_id} was there {LOST_LIMIT_SEC}s after it"
                    " stopped answering"
                )
                await asyncio.sleep(max(0.0, ABSENCE_SEC - lost_after))
                # The survivor holds on: the peer's FDB entry, its SAs, its own record.
                assert await probe.fdb_has_remote(survivor, mac_b), (
                    "the survivor dropped the peer's FDB entry while the peer was merely silent"
                )
                assert await _sa_count(survivor) == sas_before, (
                    "the survivor's XFRM state changed while its peer was silent"
                )
                assert (await session_driver.status(running.session_id)) == "RUNNING", (
                    "the session was moved out of RUNNING over a silent peer"
                )
                # The rest of the rig is untouched: a new session across the two other nodes.
                if overlay_bystander is not None:
                    async with session_driver.session(overlay_bystander, "dp-n2-bystander") as o:
                        (pid_x, _), *_ = await probe.overlay_endpoints(nodes[0], o)
                        (_, ip_y), *_ = await probe.overlay_endpoints(nodes[1], o)
                        assert await probe.reaches(nodes[0], pid_x, ip_y), (
                            "a session on the two healthy nodes could not cross the overlay while"
                            " a third node was gone"
                        )
            back_after = await _until(
                lambda: _status_is(agent_status, peer_id, "ALIVE"), limit=RETURN_LIMIT_SEC
            )
            assert back_after is not None, f"{peer_id} did not come back within {RETURN_LIMIT_SEC}s"
            reach_after = await _until(
                lambda: probe.reaches(survivor, pid_a, ip_b), limit=RETURN_LIMIT_SEC, interval=1.0
            )
            assert reach_after is not None, (
                "the session did not carry traffic again after its peer returned"
            )
            print(
                f"\nmanager marked the peer LOST after {lost_after:.0f}s; back ALIVE {back_after:.0f}s"
                f" after the cut was lifted; traffic crossed again after {reach_after:.0f}s"
            )

    async def test_n3_a_session_given_up_on_while_its_peer_is_gone_is_released_when_it_returns(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        overlay_ab: SessionSpec,
        agent_ids: tuple[str, ...],
        nodes: Sequence[Node],
        node_addresses: Sequence[str],
        agent_status: Callable[[str], Awaitable[str]],
        etcd: AsyncEtcd,
    ) -> None:
        """The case an operator meets: a node is gone, the session on it is useless, they
        terminate it. The overlay teardown declines while any node still holds the VNI, and the
        gone node cannot let go -- so what happens to the session and its allocation, both while
        the node is gone and once it is back, is measured rather than assumed."""
        peer = nodes[-1]
        peer_id = agent_ids[-1]
        home, others = node_addresses[0], [a for a in node_addresses[:-1]]
        handle = await session_driver.create(overlay_ab, "dp-n3")
        gone: str = ""
        keys_while_gone: dict[str, str] = {}
        async with _Vanished(peer, home, others):
            assert (
                await _until(
                    lambda: _status_is(agent_status, peer_id, "LOST"), limit=LOST_LIMIT_SEC
                )
                is not None
            )
            await session_driver.destroy(handle.session_id, wait=False)
            await asyncio.sleep(60.0)
            gone = await session_driver.status(handle.session_id)
            keys_while_gone = await _session_keys(etcd, handle.session_id)
        released_after = await _until(
            lambda: _released(etcd, handle.session_id), limit=RELEASE_LIMIT_SEC, interval=5.0
        )
        final = await session_driver.status(handle.session_id)
        print(
            f"\nwhile the peer was gone: session {gone}, {len(keys_while_gone)} etcd key(s) held"
            f" ({', '.join(sorted(k.rsplit('/', 2)[-2] + '/' + k.rsplit('/', 1)[-1] for k in keys_while_gone))});"
            f" after it returned: session {final}, allocation released after"
            f" {released_after if released_after is None else f'{released_after:.0f}s'}"
        )
        assert released_after is not None, (
            f"the session's allocation was never given back after its peer returned; still held:"
            f" {sorted(keys_while_gone)}"
        )
        assert final in ("TERMINATED", "CANCELLED"), f"the session ended {final}"


async def _status_is(status: Callable[[str], Awaitable[str]], agent_id: str, want: str) -> bool:
    return (await status(agent_id)).upper() == want


async def _released(etcd: AsyncEtcd, session_id: UUID) -> bool:
    return not await _session_keys(etcd, session_id)
