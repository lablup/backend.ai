"""R1. The data plane is updated one node at a time while sessions run.

The procedure an operator performs on a cluster that already runs the privileged network helper:
on each node in turn, bring the helper up on the new build, then the agent. Three things must hold
throughout, and each has been broken on this branch at some point:

- A session already running keeps carrying traffic while its node is updated, measured as the
  delivered fraction of a full-size ping stream across the overlay, sampled without pause.
- A node whose helper is down is not offered work. It says so itself, within one heartbeat, and a
  session asked for meanwhile comes up somewhere else. Nothing in the manager knows why.
- When the last node is done the cluster is whole: a new overlay session comes up across two
  updated nodes, and nothing was left behind.

Not covered here: a change one node cannot understand. That is not an update but an install, and
this scenario is about the kind that is rolled.

Gated on both restart controls (BAI_DATAPLANE_AGENT_START_CMD, BAI_DATAPLANE_PRIVNET_START_CMD).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import replace

import pytest

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.testutils.dataplane import probe
from ai.backend.testutils.dataplane.agent_control import AgentController
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.privnet_control import PrivnetController
from ai.backend.testutils.dataplane.session import SessionDriver, SessionHandle, SessionSpec

#: How long a node may take to say it is not taking work once its helper is gone: one heartbeat
#: (10s by default), with room for the event to land.
WITHDRAW_LIMIT_SEC = 30.0
#: How long the manager may take to see the node back once the helper is: the next heartbeat.
RETURN_LIMIT_SEC = 45.0
#: The stream sampled across the update. Full-size frames, because a broken underlay passes small
#: ones; the count keeps each sample short enough that no phase of the update is missed.
PING_COUNT = 40
PING_PAYLOAD = 1200
#: The whole update, end to end, must deliver at least this fraction. Not 1.0: an agent restart
#: re-adopts the session's devices, and one sample straddling that has been seen to lose a packet.
DELIVERED_FLOOR = 0.95


async def _until(
    check: Callable[[], Awaitable[bool]], *, limit: float, interval: float = 2.0
) -> bool:
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        if await check():
            return True
        await asyncio.sleep(interval)
    return await check()


class _Stream:
    """A ping stream sampled back to back for as long as the update runs."""

    def __init__(self, node: Node, pid: str, target: str) -> None:
        self._node, self._pid, self._target = node, pid, target
        self.samples: list[tuple[float, float]] = []
        self._task: asyncio.Task[None] | None = None

    async def _run(self) -> None:
        while True:
            ratio = await probe.delivery_ratio(
                self._node,
                self._pid,
                self._target,
                count=PING_COUNT,
                payload=PING_PAYLOAD,
                interval=0.05,
            )
            self.samples.append((time.monotonic(), ratio))

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    @property
    def delivered(self) -> float:
        if not self.samples:
            return 0.0
        return sum(r for _, r in self.samples) / len(self.samples)


class TestRollingUpdate:
    async def test_r1_the_rig_is_updated_one_node_at_a_time_under_load(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
        agent_ids: tuple[str, ...],
        nodes: Sequence[Node],
        node_controls: Sequence[tuple[AgentController, PrivnetController]],
        agent_status: Callable[[str], Awaitable[str]],
        client_registry: V2ClientRegistry,
    ) -> None:
        if len(nodes) < 3:
            pytest.skip("needs three nodes: two carrying an overlay session and one to roll first")
        overlay = replace(
            session_spec,
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            agent_list=agent_ids[:2],
        )
        single = replace(session_spec, cluster_size=1, cluster_mode=ClusterModeEnum.SINGLE_NODE)
        withdrawn: dict[str, str] = {}
        landed: dict[str, list[str]] = {}
        async with session_driver.session(overlay, "dp-r1-overlay") as running:
            node_a, node_b = nodes[0], nodes[1]
            (pid_a, ip_a), *_ = await probe.overlay_endpoints(node_a, running)
            (_pid_b, ip_b), *_ = await probe.overlay_endpoints(node_b, running)
            assert await probe.reaches(node_a, pid_a, ip_b), (
                f"{ip_a} could not reach {ip_b} before the update; the stream would measure a"
                " session that never worked"
            )
            stream = _Stream(node_a, pid_a, ip_b)
            stream.start()
            try:
                for index, (agent, privnet) in enumerate(node_controls):
                    agent_id = agent_ids[index]
                    # The helper goes down on the new build.
                    await privnet.kill()
                    assert await _until(
                        lambda: _not_alive(agent_status, agent_id), limit=WITHDRAW_LIMIT_SEC
                    ), (
                        f"agent {agent_id} was still offered work {WITHDRAW_LIMIT_SEC}s after its"
                        " privileged network helper went down"
                    )
                    withdrawn[agent_id] = await agent_status(agent_id)
                    # Work asked for meanwhile lands on a node that can take it.
                    mid = await session_driver.create(single, f"dp-r1-mid-{index}")
                    try:
                        placed = list(await _agents_of(client_registry, mid))
                        landed[agent_id] = placed
                        assert placed and agent_id not in placed, (
                            f"a session requested while {agent_id}'s helper was down was placed on"
                            f" {placed}; the node was still being offered work"
                        )
                    finally:
                        await session_driver.destroy(mid.session_id)
                    # The helper is back; the node announces itself again.
                    await privnet.start()
                    assert await _until(
                        lambda: _alive(agent_status, agent_id), limit=RETURN_LIMIT_SEC
                    ), (
                        f"agent {agent_id} did not come back within {RETURN_LIMIT_SEC}s of its helper"
                    )
                    # Then the agent, on the new build, adopting what is running.
                    await agent.restart()
                    assert await _until(
                        lambda: _alive(agent_status, agent_id), limit=RETURN_LIMIT_SEC
                    ), f"agent {agent_id} did not report in after its restart"
            finally:
                await stream.stop()
            assert stream.samples, "the stream never produced a sample"
            assert stream.delivered >= DELIVERED_FLOOR, (
                f"the running overlay session delivered {stream.delivered:.3f} of its stream across"
                f" the update (floor {DELIVERED_FLOOR}); per sample: "
                + ", ".join(f"{r:.2f}" for _, r in stream.samples)
            )
        # The cluster is whole: a fresh overlay session across two updated nodes.
        async with session_driver.session(overlay, "dp-r1-after") as fresh:
            (pid_after, _), *_ = await probe.overlay_endpoints(node_a, fresh)
            (_, ip_after), *_ = await probe.overlay_endpoints(node_b, fresh)
            assert await probe.reaches(node_a, pid_after, ip_after), (
                "a session created after the update cannot cross the overlay"
            )
        print(
            f"\nwithdrawn as: {withdrawn}\nmid-update sessions landed on: {landed}\n"
            f"stream delivered {stream.delivered:.3f} over {len(stream.samples)} samples"
        )


async def _not_alive(status: Callable[[str], Awaitable[str]], agent_id: str) -> bool:
    return (await status(agent_id)).upper() != "ALIVE"


async def _alive(status: Callable[[str], Awaitable[str]], agent_id: str) -> bool:
    return (await status(agent_id)).upper() == "ALIVE"


async def _agents_of(registry: V2ClientRegistry, handle: SessionHandle) -> Sequence[str]:
    """The agents the session's kernels were placed on, from the kernels themselves."""
    found = await registry.session.search_kernels_by_session(
        str(handle.session_id), AdminSearchKernelsInput()
    )
    return tuple(
        kernel.resource.agent_id for kernel in found.items if kernel.resource.agent_id is not None
    )
